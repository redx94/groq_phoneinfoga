
{ pkgs }: {
  deps = [
    pkgs.python3
    pkgs.python311Packages.phonenumbers
    pkgs.python311Packages.requests
    pkgs.python311Packages.beautifulsoup4
  ];
}
