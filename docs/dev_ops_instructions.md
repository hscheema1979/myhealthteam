# DevOps Instructions for Latest Git Changes

## Overview
This document outlines the steps required to deploy the latest changes to the production environment. The changes include new billing features, dashboard enhancements, and cleanup.

## Current Git Status
- **Branch:** main
- **Commit:** 3ff62fe0daaa5b87db1ace509d33fef4ae3aac2f
- **Date:** Thu Dec 4 17:03:23 2025 -0800
- **Author:** hscheema <hscheema@gmail.com>
- **Commit Message:** Comprehensive update: New billing features, dashboard enhancements, and cleanup

## Steps to Deploy

### 1. Pull Latest Changes on Production Server
- **SSH into the production server:**
  ```sh
  ssh user@prod-server-ip
  ```
- **Navigate to the project directory:**
  ```sh
  cd /path/to/project
  ```
- **Pull the latest changes from the main branch:**
  ```sh
  git pull origin main
  ```

### 2. Restart the Service
- **Restart the service to apply the changes:**
  ```sh
  sudo systemctl restart service-name
  ```
  - Replace `service-name` with the actual name of your service.

### 3. Verify the Deployment
- **Check the service status to ensure it is running:**
  ```sh
  sudo systemctl status service-name
  ```
- **Verify the changes by accessing the application:**
  - Open the application in a web browser or use a tool like `curl` to check the endpoints.

## Additional Notes
- **Backup:** Ensure you have a backup of the current production environment before making any changes.
- **Monitoring:** Monitor the application for any issues after the deployment.
- **Logs:** Check the application logs for any errors or warnings.

## Contact Information
- **Developer:** hscheema <hscheema@gmail.com>
- **Support:** support@myhealthteam.com
