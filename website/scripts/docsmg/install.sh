cargo install --git https://github.com/goauthentik/authentik
sudo wget https://raw.githubusercontent.com/goauthentik/authentik/main/website/scripts/docsmg/m.bash -O /bin/map
sudo wget https://raw.githubusercontent.com/goauthentik/authentik/main/website/scripts/docsmg/mcomplete.bash -O /bin/mapcomplete
sudo chmod 755 /bin/map
echo "source mapcomplete" >> ~/.zshrc
