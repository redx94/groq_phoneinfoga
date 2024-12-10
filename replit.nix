{ pkgs }: {
  deps = [
    pkgs.python3Packages.phonenumbers
    pkgs.python3Packages.requests
    pkgs.python3Packages.beautifulsoup4
  ];
}