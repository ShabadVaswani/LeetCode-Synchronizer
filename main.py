def sync_github(commits, submissions):
    repo = Repo(os.getcwd())
    url = urllib.parse.urlparse(repo.remote("origin").url)
    url = url._replace(netloc=f"{os.environ.get('GITHUB_TOKEN')}@" + url.netloc)
    url = url._replace(path=url.path + ".git")
    repo.remote("origin").set_url(url.geturl())

    commit = list(repo.iter_commits())[0]
    repo.config_writer().set_value("user", "name", commit.author.name).release()
    repo.config_writer().set_value("user", "email", commit.author.email).release()

    for submission in submissions:
        commit_message = f"LeetCode Synchronization - {submission['title']} ({submission['language']})"
        if commit_message not in commits or commits[commit_message] < submission["timestamp"]:
            dir_name = f"{str(submission['id']).zfill(4)}-{submission['title_slug']}"
            
            # Skip Java submissions
            if submission["language"] == "Java":
                print(f"Skipping Java submission: {submission['title']}")
                continue

            if submission["language"] == "C++":
                ext = "cpp"
            elif submission["language"] == "MySQL":
                ext = "sql"
            elif submission["language"] == "Bash":
                ext = "sh"
            else:
                print(f"Skipping unsupported language: {submission['language']}")
                continue

            pathlib.Path(f"problems/{dir_name}").mkdir(parents=True, exist_ok=True)
            with open(f"problems/{dir_name}/{dir_name}.{ext}", "wt") as fd:
                fd.write(submission["code"].strip())
            with open(f"problems/{dir_name}/README.md", "wt") as fd:
                content = f"<h2>{submission['id']}. {submission['title']}</h2>\n\n"
                content += submission["content"].strip()
                fd.write(content)

            submission["skills"].sort()
            new_submission = {
                "id": submission["id"],
                "title": submission["title"],
                "title_slug": submission["title_slug"],
                "difficulty": submission["difficulty"],
                "skills": submission["skills"],
            }

            saved_submissions = list()
            if os.path.isfile("submissions.json"):
                with open("submissions.json", "rt") as fd:
                    saved_submissions = json.load(fd)

            if new_submission not in saved_submissions:
                saved_submissions.append(new_submission)
                saved_submissions = sorted(saved_submissions, key=lambda entry: entry["id"])
                update_readme(saved_submissions)
                with open("submissions.json", "wt") as fd:
                    json.dump(saved_submissions, fd, ensure_ascii=False, indent=2)

            # RFC 2822 (Thu, 07 Apr 2005 22:13:13 +0200) / ISO 8601 (2005-04-07T22:13:13)
            # https://github.com/gitpython-developers/GitPython/blob/master/git/objects/util.py#L134
            iso_datetime = email.utils.format_datetime(datetime.datetime.fromtimestamp(submission["timestamp"]))
            os.environ["GIT_AUTHOR_DATE"] = iso_datetime
            os.environ["GIT_COMMITTER_DATE"] = iso_datetime
            repo.index.add("**")
            repo.index.commit(commit_message)
            repo.git.push("origin")
            os.unsetenv("GIT_AUTHOR_DATE")
            os.unsetenv("GIT_COMMITTER_DATE")
