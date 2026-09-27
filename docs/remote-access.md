# Letting friends outside your network join

## Current state and test limits

The server publishes only `127.0.0.1:25565`; the dashboard listens only on `127.0.0.1:8765`. RCON is not published. This deliberately prevents direct LAN/internet access even if someone knows the public IP. The public IP was obtained privately with ipify; it is not stored in the repository because it identifies the household connection and can change.

A TCP probe from this laptop reached the local Minecraft port. Probes to this connection's public IP on 25565 and 8765 timed out. This is a same-network/NAT-loopback test, **not an independent outside-network test**. No router settings, firewall rules, public binds or port forwards were changed. We cannot establish CGNAT status without comparing the router's WAN address with the public IP, and cannot conclude external reachability from this test alone.

## Recommended: private VPN for invited friends

[Tailscale's private game-server guide](https://tailscale.com/docs/use-cases/personal-or-at-home-use/share-private-game-server) supports device sharing and encrypted connections without public router forwarding. Each friend needs the VPN client/account, but no management-website account. Keep Minecraft's own online-mode authentication and allowlist too.

For this macOS/Docker arrangement, the current localhost bind needs deliberate integration: either an authenticated tailnet-only TCP forwarding endpoint to 127.0.0.1:25565, or a reviewed Docker bind to a reachable host interface restricted by the VPN/firewall. Verify the selected approach on macOS; do not assume binding a container port to a VPN address works automatically. Limit the VPN access policy to the game port and intended people. Do not share the dashboard, RCON, filesystem, Docker socket or broad access to other laptop services. Do not use a public “Funnel” endpoint for a private-only design.

The next setup decision is whether all players can use Tailscale. If yes, configure the devices/sharing and narrow policy, then test from a friend's network or mobile hotspot: allowed account can join, non-allowlisted authenticated account cannot, and dashboard/RCON remain unreachable.

## Alternative: public game endpoint

If players cannot install a VPN, a public TCP tunnel or router port-forward can provide a game address. This makes the Minecraft port reachable by strangers; online-mode plus the allowlist must still reject their admission. It is not the same as keeping the game port private.

Router forwarding requires control of the router, a stable local address, a reviewed non-loopback game bind, and a public WAN address (CGNAT/double NAT can prevent direct forwarding). Forward **only TCP 25565**. Never forward 8765, RCON 25575, Docker ports, or use router DMZ mode. Dynamic DNS may be needed if the ISP changes the public IP. A tunnel provider adds a third party, possible limits/costs and a separate trust decision. Keep backups and updates current.

Neither option is configured automatically by this repository. A separate outside-network connection test is required after selecting and implementing the access path. The Minecraft allowlist stays mandatory in every case.
