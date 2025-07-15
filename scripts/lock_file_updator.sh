git switch main
git pull origin main --rebase

git switch --force-create lock_file/weekly-upgrade

output="$(uv lock -U 2>&1)"

git add uv.lock
git commit -m "chore(lock_file): Weekly lock file upgrade" -m "This PR upgrades uv lock file.$output"
git push --force
