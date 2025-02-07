import os
import argparse
import requests
from datetime import datetime

# This script fetches all releases in github for a certain organization using the github token stored in the environment
# variable GITHUB_TOKEN. Example call
#
# python github-releases.py --from-date 2024-01-01 --to-date 2025-01-01 --org budbee --author jesper-budbee --detailed

def print_release_details(repo_releases, repo_name, print_detailed, print_repo_name):
    r = len(repo_name)/2
    l = int(60 - r)
    if print_repo_name or print_detailed:
        if print_detailed:
            print(f"\n{'='*l} {repo_name} {'='*l}")
        else:
            print(f"{repo_name}")
    for release in repo_releases:
        created_at = datetime.strptime(release["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        formatted_created_at = created_at.strftime("%Y-%m-%d %H:%M")
        if print_detailed:
            print(""
                  f"      Name: {release['name']}\n"
                  f"    Author: {release['author']['login']}\n"
                  f"   Created: {formatted_created_at}\n"
                  f"Repository: {repo_name}\n"
                  f"\n{release['body']}\n"
                  f"{'-'*120}"
                  "")
        else:
            print(f"    {formatted_created_at}: {release['name']} by {release['author']['login']}")

    if print_repo_name or print_detailed:
        print("\n")

def get_releases_on_date(org_name, from_date, to_date, token, print_details, author):
    all_releases = {}
    page = 0
    repos = []
    new_repos = ["dummy"]
    while new_repos:
        page += 1
        releases_url = f"https://api.github.com/orgs/{org_name}/repos?per_page=100&page={page}"
        response = requests.get(releases_url, headers={"Accept": "application/vnd.github+json", "Authorization": f"token {token}"})
        response.raise_for_status()
        new_repos = response.json()
        repos.extend(new_repos)
    print(f"Found {len(repos)} repos")

    repos = sorted(repos, key=lambda repo: repo["name"])
    print(f"Will start looking for releases in org {org_name} between {from_date.date()} and {to_date.date()} (both inclusive)\n")
    for idx, repo in enumerate(repos):
        print(f"{idx}/{len(repos)}: {repo['name']}")
        releases_url = repo["releases_url"].replace("{/id}", "")
        releases_response = requests.get(releases_url, headers={"Accept": "application/vnd.github+json", "Authorization": f"token {token}"})
        releases_response.raise_for_status()
        releases = releases_response.json()
        releases = sorted(releases, key=lambda release: release["created_at"])
        repo_releases = []
        for release in releases:
            created_at = datetime.strptime(release["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            valid_date = from_date.date() <= created_at.date() <= to_date.date()
            valid_author = not author or (release["author"] and author == release["author"]["login"])
            if valid_date and valid_author:
                repo_releases.append(release)
        if repo_releases:
            print_release_details(repo_releases, repo["name"], print_details, False)
            all_releases[repo["name"]] = repo_releases
    return all_releases


def run():
    parser = argparse.ArgumentParser(description="Get GitHub releases on a specific date range.")
    parser.add_argument("--from-date", required=True, type=str, help="The start date in YYYY-MM-DD format")
    parser.add_argument("--to-date", required=True, type=str, help="The end date in YYYY-MM-DD format")
    parser.add_argument("--org", required=True, type=str, help="The org to search in")
    parser.add_argument("--author", required=False, type=str, help="The org to search in")

    parser.add_argument(
        "--detailed",
        action='store_true',
        help="If set, will print detailed information about the release"
    )
    args = parser.parse_args()

    from_date = datetime.strptime(args.from_date, "%Y-%m-%d")
    to_date = datetime.strptime(args.to_date, "%Y-%m-%d")
    author = args.author
    token = os.getenv('GITHUB_TOKEN')
    print_details = args.detailed
    matched_releases = get_releases_on_date(args.org, from_date, to_date, token, print_details, author)
    number_of_releases = sum(len(r) for r in matched_releases.values())
    print(f"\n\n\nFound {str(number_of_releases)} release(s) in {str(len(matched_releases.keys()))} repo(s) in org {args.org} between {from_date.date()} and {to_date.date()} (both inclusive).")
    for repo, releases in matched_releases.items():
        print(f"    - {len(releases)} releases in {repo}")

    print("\n\n\n")
    for repo, releases in matched_releases.items():
        print_release_details(releases, repo, print_details, True)

if __name__ == "__main__":
    run()
