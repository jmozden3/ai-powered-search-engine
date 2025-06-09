# ai-powered-search-engine

## Pre-reqs
- Create all Azure resources in South Central US region
- Services needed:
   - Azure SQL server and a database
   - Azure OpenAI
   - Azure AI search (standard tier) 

## Setup
1. Azure OpenAI
   - Need a text-embedding-ada-002 model deployed
2. Azure AI Search
   - May need system-assigned identity turned on in your search service
   - Grant the Azure identity (eg your user id) "Search Index Data Contributor" role on your Search Service. If using Azure AD authentication, you may also need to at the "Search Service Contributor" role.
3. Azure SQL server
   - Settings > Microsoft Entra ID > ensure 'Microsoft Entra authentication only' is UNchecked (note: sometimes SQL server will recheck this box and you may get errors when trying to access your db programtically...when this happens, go to your SQL server resource in the Azure portal and just UNcheck it again)
   - Security > Networking > under 'firewall rules', add your client IPv4 address
4. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
2. Copy `sample.env` to `.env` and fill in your Azure credentials and configuration values.
3. Ensure Azure SQL database is accessible and contains the `EnforcementActions` table.