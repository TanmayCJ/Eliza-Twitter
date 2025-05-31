# CarbonTruth Bot Setup Guide

This guide will walk you through setting up and running the CarbonTruth bot from the ElizaBots project.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Setup Instructions](#setup-instructions)
3. [Environment Configuration](#9-configure-environment-variables)
4. [Running the Bot](#10-start-the-bot)
5. [Troubleshooting](#troubleshooting)


## Prerequisites

- Windows 10/11 or Linux or Mac
- Node.js 23.3+
- Git

> **💡 Windows Users:** It's recommended to use **Git Bash** instead of Command Prompt or PowerShell for better compatibility with the setup commands. If you encounter issues with CMD or PowerShell, switch to Git Bash which comes bundled with Git for Windows.

## Setup Instructions

### 1. Clone Repository

Clone the CarbonTruth repository from GitHub:

```powershell
git clone https://github.com/CarbonSustain/carbontruth.git
```

### 2. Navigate to CarbonTruth Directory

Change to the CarbonTruth project directory:

```powershell
cd carbontruth/ElizaBots/CarbonTruth
```

### 3. Verify Node.js Version

Ensure you have Node.js version 23.3+ installed:

```powershell
node --version
```

**If you don't have Node.js 23.3+ installed:**

Download and install from [nodejs.org](https://nodejs.org/en/download) or use Windows Package Manager:


### 4. Install pnpm Package Manager

Install pnpm globally:

```powershell
npm install -g pnpm
```

Verify the installation:

```powershell
pnpm --version
```

### 5. Install Project Dependencies

Install all required dependencies:

```powershell
pnpm install
```

**If you encounter a "no lock file" error:**

```powershell
pnpm install --no-frozen-lockfile
```
> This tells pnpm to proceed without relying on a `pnpm-lock.yaml` file.

### 6. Fix Line Endings (Windows Only)

For Windows users, convert shell script line endings:

1. Open `client/version.sh` in VS Code
2. Look at the bottom-right status bar - you'll see "CRLF"
3. Click on "CRLF"
4. Select "LF" from the dropdown menu
5. Save the file (`Ctrl+S`)

This converts Windows line endings (CRLF) to Unix line endings (LF) required for shell scripts.

### 7. Build the Project

Compile the project:

```powershell
pnpm build
```

### 8. Setup Environment Configuration

Copy the example environment file:

**PowerShell/CMD:**

```powershell
copy .env.example .env
```

**GitBash/Linux:**

```bash
cp .env.example .env
```

### 9. Configure Environment Variables

Open the `.env` file in your editor and configure the following variables:

```env
# Twitter Credentials
TWITTER_USERNAME=    # Your Twitter account username
TWITTER_PASSWORD=    # Your Twitter account password
TWITTER_EMAIL=       # Your Twitter account email

# OpenAI Configuration
OPENAI_API_KEY=      # Your OpenAI API key

# Additional API Keys
TOGETHER_API_KEY=    # Together AI API key
GROQ_API_KEY=        # Groq API key 
TINY_URL_API_KEY=    # TinyURL API key
PEXEL_API_KEY=       # Pexels API key
```

>**Note**: The API keys mentioned above are essential for the bot to function properly. Other parameters are optional and can be ignored.

### 10. Start the Bot

Launch the CarbonTruth bot:

```powershell
pnpm start --characters="characters\CarbonTruth.json"
```

The `--characters` flag specifies the character configuration to load. You can customize or add your own JSON files in the `characters/` directory.

> You should see logs in the terminal indicating that the bot has started and connected successfully. If not, revisit the `.env` configuration and check the logs for any errors.


## Troubleshooting

- **Build errors:** Ensure all dependencies are installed and Node.js version is correct
- **Permission errors:** Run PowerShell as Administrator if needed
- **Line ending issues:** Make sure to convert `version.sh` from CRLF to LF on Windows
- **Environment errors:** Verify all required API keys are properly configured in `.env`
- **Terminal compatibility issues:** If you encounter errors with PowerShell or CMD, switch to **Git Bash** for better Unix command compatibility



