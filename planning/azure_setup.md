Azure Setup

## Phase 1: Create Azure OpenAI Resource (The "Brain")

1. **Log in to Azure Portal:** Go to [portal.azure.com](https://portal.azure.com).
2. **Search:** In the top search bar, type **"Azure OpenAI"** and select it.
3. **Create:** Click **+ Create**.
4. **Fill Details:**
    - **Subscription:** Select your subscription (e.g., "Azure for Students" or "Pay-As-You-Go").
    - **Resource Group:** Click **Create new** → Name it `rg-cyderes-aegis` (we'll put everything here).
    - **Region:** Choose **East US 2** or **Sweden Central** (these have the best GPT-4o availability).
    - **Name:** Enter a unique name, e.g., `oai-aegis-shashank` (if taken, add random numbers).
    - **Pricing Tier:** Select **Standard S0**.
5. **Review \& Submit:** Click **Next** until **Create**. Wait 2-3 minutes for deployment.

### Get Key \& Endpoint

1. Go to your new resource (`oai-aegis-shashank`).
2. Left Menu → **Resource Management** → **Keys and Endpoint**.
3. **Copy KEY 1** → This is `AZURE_OPENAI_API_KEY`.
4. **Copy Endpoint** (e.g., `https://oai-aegis-shashank.openai.azure.com/`) → This is `AZURE_OPENAI_ENDPOINT`.

### Deploy Models (Critical Step)

The resource is empty until you deploy a model.

1. In your resource, click **"Go to Azure AI Foundry portal"** (top button).
2. Left Menu → **Deployments** → **+ Deploy model** → **Deploy base model**.
3. **Model 1 (Manager/Analyst):**
    - Select **gpt-4o**.
    - Deployment name: **gpt-4o** (Keep it exactly this name).
    - Version: Select latest (e.g., `2024-08-06` or `2024-05-13`).
    - Click **Deploy**.
4. **Model 2 (Intel Agent - Cost Saver):**
    - Click **+ Deploy model** again.
    - Select **gpt-4o-mini**.
    - Deployment name: **gpt-4o-mini**.
    - Click **Deploy**.

***

## Phase 2: Create Azure Storage Account (The "Data Lake")

1. Search **"Storage accounts"** in Azure Portal.
2. Click **+ Create**.
3. **Basics:**
    - Resource Group: `rg-cyderes-aegis`.
    - Name: `stcyderesaegis` (must be lowercase, no symbols, unique globally).
    - Region: Same as OpenAI (e.g., **East US 2**).
    - Performance: **Standard**.
    - Redundancy: **LRS** (Locally-redundant storage) -> *Cheapest option*.
4. Click **Review + create** → **Create**.

### Get Connection String

1. Go to the new storage account.
2. Left Menu → **Security + networking** → **Access keys**.
3. Under **key1**, click **Show** next to **Connection string**.
4. **Copy it** → This is `AZURE_STORAGE_CONNECTION_STRING`.

### Create the Container

1. Left Menu → **Data storage** → **Containers**.
2. Click **+ Container**.
3. Name: `security-logs`.
4. Click **Create**.
5. **Upload Data:** Click into `security-logs` → **Upload** → Select your local `data/raw/firewall_logs.csv` file.

***

## Phase 3: Create Azure Cosmos DB (The "Memory")

1. Search **"Azure Cosmos DB"** in Azure Portal.
2. Click **+ Create**.
3. Select **Azure Cosmos DB for NoSQL** (Click "Create" on that tile).
4. **Basics:**
    - Resource Group: `rg-cyderes-aegis`.
    - Account Name: `cosmos-aegis-shashank`.
    - Region: Same as others.
    - Capacity mode: **Serverless** (Best for low traffic/dev) OR **Provisioned throughput** with "Free Tier Discount" checked if available. *Serverless is safer for budget if Free Tier isn't available.*
5. Click **Review + create** → **Create**. (Takes ~5-10 mins).

### Get Keys

1. Go to the resource.
2. Left Menu → **Settings** → **Keys**.
3. **Copy URI** → This is `COSMOS_ENDPOINT`.
4. **Copy PRIMARY KEY** → This is `COSMOS_KEY`.

### Create Database \& Container

1. Left Menu → **Data Explorer**.
2. Click **New Container**.
    - Database id: `Create new` → `aegis-swarm`.
    - Container id: `investigation-state`.
    - Partition key: `/incident_id`.
3. Click **OK**.

***

## Phase 4: Finalize `local.settings.json`

Now, open your `local.settings.json` file locally and paste the real values. It should look like this:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsFeatureFlags": "EnableWorkerIndexing",
    
    "AZURE_OPENAI_API_KEY": "paste-your-key-1-here",
    "AZURE_OPENAI_ENDPOINT": "https://oai-aegis-shashank.openai.azure.com/",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4o",
    "AZURE_OPENAI_API_VERSION": "2024-08-01-preview",
    
    "AZURE_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https;AccountName=stcyderesaegis;AccountKey=...;EndpointSuffix=core.windows.net",
    "AZURE_STORAGE_CONTAINER_NAME": "security-logs",
    
    "COSMOS_ENDPOINT": "https://cosmos-aegis-shashank.documents.azure.com:443/",
    "COSMOS_KEY": "paste-your-primary-key-here",
    "COSMOS_DATABASE_NAME": "aegis-swarm",
    "COSMOS_CONTAINER_NAME": "investigation-state",
    
    "MANAGER_MODEL": "gpt-4o",
    "ANALYST_MODEL": "gpt-4o",
    "INTEL_MODEL": "gpt-4o-mini",
    "MAX_INVESTIGATION_LOOPS": "10"
  }
}
```


## Phase 5: Re-run the Tests

1. Save `local.settings.json`.
2. Stop the running `func start` (Ctrl+C).
3. Start it again:

```bash
func start
```

4. Run the test script in a new terminal:

```bash
python scripts/test_analyst.py
```


**Why this will fix it:**
The "Connection error" meant your Python code tried to call `https://your-resource.openai.azure.com/` (a fake URL). Now it will call your actual Azure resource with a valid key.

Go ahead and set these up. Let me know if you get stuck on any specific Azure Portal step!
<span style="display:none">[^1][^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^2][^20][^3][^4][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: i-am-giving-you-my-conventions-_3qgJk0sSPmdEP41ieCTtg.md

[^2]: new_project_brief.md

[^3]: project_details.md

[^4]: conventions.md

[^5]: deploment_guide.md

[^6]: https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/create-resource

[^7]: https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/create-resource?view=foundry-classic

[^8]: https://www.youtube.com/watch?v=XqoqgIZS2rc

[^9]: https://devblogs.dewiride.com/blog/creating-azure-openai-resource-and-deploying-models-step-by-step-guide

[^10]: https://k21academy.com/ai-ml/azure/create-azure-openai-service-resources-using-console-cli-step-by-step-activity-guide/

[^11]: https://www.librechat.ai/docs/configuration/azure

[^12]: https://github.com/Azure/azure-sdk-for-net/blob/main/sdk/openai/Azure.AI.OpenAI/CHANGELOG.md

[^13]: https://www.datacamp.com/tutorial/azure-openai

[^14]: https://docs.litellm.ai/docs/providers/azure/

[^15]: https://www.reddit.com/r/AZURE/comments/1liihxf/unable_to_figure_out_the_correct_api_version/

[^16]: https://devopscube.com/setup-azure-openai/

[^17]: https://stackoverflow.com/questions/76589496/endpoint-for-azure-model

[^18]: https://stackoverflow.com/questions/76475419/how-can-i-select-the-proper-openai-api-version/76476951

[^19]: https://www.youtube.com/watch?v=dh-5uLY5z84

[^20]: https://docs.spring.io/spring-ai/reference/api/chat/azure-openai-chat.html

