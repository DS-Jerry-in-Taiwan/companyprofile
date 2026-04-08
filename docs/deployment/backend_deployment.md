# Backend Deployment

## AWS MFA Temporary Credentials

To enable AWS MFA temporary credentials for the backend deployment:

1. Configure your AWS account to require MFA for administrative actions.
2. Obtain an MFA device and associate it with your AWS IAM user.
3. Update the deployment scripts to use the `aws sts get-session-token` command, passing in your MFA device code.
4. Ensure the deployment process can successfully authenticate with the temporary credentials.
