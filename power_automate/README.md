# Power Automate Pack

This folder contains a portfolio-ready reference flow for the Microsoft automation layer.

Suggested production flow:
1. Receive the webhook payload from `AlertRouter`.
2. Branch by `team` and `severity`.
3. Post a Teams message to the owning operations channel.
4. Write the exception to SharePoint or Dataverse for auditability.
5. Notify the on-call distribution list for high-severity incidents.
6. Optionally open an approval or remediation task in Planner.

Use `exception_alert_flow.json` as the import/reference template when recreating the flow in Power Automate.

