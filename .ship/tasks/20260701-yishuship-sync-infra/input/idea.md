# Original Idea

User wants yishuship refreshed to the latest `https://github.com/yishu-ziyu/ship.git` version and used inside Claude Code.

The deeper goal is to build stable collaboration infrastructure between the user and AI agents:

- Claude Code should reliably expose `/yishuship:*` skills.
- Local installation should stay close to the latest `yishu-ziyu/ship` repository updates.
- Session startup should surface current working directory, project, progress, and next suggested step.
- Real-time updates across repository state, plugin installation, project `.ship` state, and durable memory should have minimal delay.
- Avoid confusion between original `heliohq/ship`, older local simplified commands, and the user's own yishuship fork.
