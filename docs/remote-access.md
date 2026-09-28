# Letting friends outside your network join

## Current state and test limits

On 2026-09-27 the owner confirmed router forwarding and a WAN address matching the public IPv4 address. The running profile was changed to bind TCP 25565 to the laptop's LAN IPv4 address in `config.yml`, with `allow_lan: true`, and gracefully restarted. The local dashboard was restarted with the same configuration and still listens only on `127.0.0.1:8765`. RCON is not published.

Minecraft protocol status requests succeeded through both the laptop's LAN address and the public forwarded address, returning Minecraft 1.20.1 / protocol 763. Public probes to 8765 and 25575 did not connect. These probes originate on the laptop (NAT loopback); an independent outside-network join test is still required. No router settings were changed by the agent; the owner configured the forwarding.

Live security verification passed after restart: online-mode, enforced allowlist and secure profiles enabled, exactly three approved players, expected game binding, and no management ports published by Docker. Authentication protects admission to the world; the public game port is reachable by anyone for connection attempts/status queries.

### Connect and maintain the forwarding

- Share the router's current public IPv4 address followed by `:25565` privately with the approved players. The public address is intentionally not recorded here.
- Use Minecraft Java 1.20.1 with a matching Forge/client mod setup. The full requested modpack is still not installed or validated.
- Reserve the laptop's current LAN address in the router's DHCP settings. The forwarding target and `server.bind_address` must match it. Do not set the host bind to the public WAN address.
- Keep only TCP 25565 forwarded. Do not forward 8765, 25575, Docker ports or enable router DMZ mode.
- Keep the laptop awake and Docker/game running. Changes to the ISP's public address require sharing the new address or configuring dynamic DNS.
- Verify from a friend's network or a mobile hotspot: approved account joins, non-allowlisted authenticated account is rejected, and management ports remain unreachable.
- To disable remote access, delete/disable the router rule, set `server.bind_address` to `127.0.0.1` and `server.allow_lan` to `false`, gracefully restart the game, and restart the dashboard so its controls use the same configuration.

## Optional future alternative: private VPN for invited friends

[Tailscale's private game-server guide](https://tailscale.com/docs/use-cases/personal-or-at-home-use/share-private-game-server) supports device sharing and encrypted connections without public router forwarding. Each friend needs the VPN client/account, but no management-website account. Keep Minecraft's own online-mode authentication and allowlist too.

If switching to a private VPN, remove the public forward and review the game binding. For this macOS/Docker arrangement, options include: either an authenticated tailnet-only TCP forwarding endpoint to 127.0.0.1:25565, or a reviewed Docker bind to a reachable host interface restricted by the VPN/firewall. Verify the selected approach on macOS; do not assume binding a container port to a VPN address works automatically. Limit the VPN access policy to the game port and intended people. Do not share the dashboard, RCON, filesystem, Docker socket or broad access to other laptop services. Do not use a public “Funnel” endpoint for a private-only design.

The next setup decision is whether all players can use Tailscale. If yes, configure the devices/sharing and narrow policy, then test from a friend's network or mobile hotspot: allowed account can join, non-allowlisted authenticated account cannot, and dashboard/RCON remain unreachable.

## Alternative: public game endpoint

If players cannot install a VPN, a public TCP tunnel or router port-forward can provide a game address. This makes the Minecraft port reachable by strangers; online-mode plus the allowlist must still reject their admission. It is not the same as keeping the game port private.

Router forwarding requires control of the router, a stable local address, a reviewed non-loopback game bind, and a public WAN address (CGNAT/double NAT can prevent direct forwarding). Forward **only TCP 25565**. Never forward 8765, RCON 25575, Docker ports, or use router DMZ mode. Dynamic DNS may be needed if the ISP changes the public IP. A tunnel provider adds a third party, possible limits/costs and a separate trust decision. Keep backups and updates current.

Router forwarding is now owner-configured as described above. A separate outside-network connection test is still required. The Minecraft allowlist stays mandatory in every case.
