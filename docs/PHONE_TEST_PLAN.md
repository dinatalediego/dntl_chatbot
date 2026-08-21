# WhatsApp phone test plan

1. First validate the full cycle with `MESSAGE_PROVIDER=mock`.
2. Then configure Meta WhatsApp Cloud API and use Meta's provided **test business phone number** as the sender/bot.
3. Add one of your own WhatsApp numbers as an allowed test recipient and use that phone as the lead.
4. Your second personal phone is optional for another test identity; you do **not** need to buy a third physical SIM just to perform the first Cloud API test.
5. Only after this works, decide whether production gets a dedicated business number or uses an eligible coexistence/migration path.

Acceptance: outbound arrives, inbound reaches `/webhooks/meta`, provider message ID/status is recorded, NIDO replies, and opt-out works.
