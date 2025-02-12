"""Script to initialize checklist items in the database."""
from app.services.db_service import DatabaseService
import os
from dotenv import load_dotenv

# Initial checklist items data
CHECKLIST_ITEMS = [
    {
        "item_id": "1.1",
        "category": "Data collection",
        "question": "Does the paper provide details about the data collection procedure, including the instruments or devices used to record the data?",
        "original": "Provide details about the data collection procedure, including the instruments or devices used to record the data (e.g. pen and paper, computer, eye tracker, video or audio equipment) whether anyone was present besides the participant(s) and the researcher, and whether the researcher was blind to experimental condition and/or the study hypothesis during data collection.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "1.2",
        "category": "Data collection",
        "question": "Does the paper specify whether anyone other than the participant(s) and the researcher was present during data collection?",
        "original": "Provide details about the data collection procedure, including the instruments or devices used to record the data (e.g. pen and paper, computer, eye tracker, video or audio equipment) whether anyone was present besides the participant(s) and the researcher, and whether the researcher was blind to experimental condition and/or the study hypothesis during data collection.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "1.3",
        "category": "Data collection",
        "question": "Does the paper state whether the researcher was blind to the experimental condition and/or the study hypothesis during data collection?",
        "original": "Provide details about the data collection procedure, including the instruments or devices used to record the data (e.g. pen and paper, computer, eye tracker, video or audio equipment) whether anyone was present besides the participant(s) and the researcher, and whether the researcher was blind to experimental condition and/or the study hypothesis during data collection.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "2.1",
        "category": "Randomization",
        "question": "Does the paper specify whether participants were allocated into experimental groups?",
        "original": "If participants were not allocated into experimental groups, state so OR describe how participants were allocated to groups, and if allocation was not random, describe how covariates were controlled.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "2.2",
        "category": "Randomization",
        "question": "If participants were allocated into groups, does the paper state whether allocation was random?",
        "original": "If participants were not allocated into experimental groups, state so OR describe how participants were allocated to groups, and if allocation was not random, describe how covariates were controlled.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "2.3",
        "category": "Randomization",
        "question": "If allocation was not random, does the paper describe how covariates were controlled?",
        "original": "If participants were not allocated into experimental groups, state so OR describe how participants were allocated to groups, and if allocation was not random, describe how covariates were controlled.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "4.1",
        "category": "Timing",
        "question": "Does the paper indicate the start and stop dates of data collection?",
        "original": "Indicate the start and stop dates of data collection. If there is a gap between collection periods, state the dates for each sample cohort.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "4.2",
        "category": "Timing",
        "question": "If there was a gap between collection periods, does the paper state the dates for each sample cohort?",
        "original": "Indicate the start and stop dates of data collection. If there is a gap between collection periods, state the dates for each sample cohort.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "5.1",
        "category": "Non-participation",
        "question": "Does the paper specify how many participants dropped out or declined participation?",
        "original": "State how many participants dropped out/declined participation and the reason(s) given OR provide response rate OR state that no participants dropped out/declined participation.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "5.2",
        "category": "Non-participation",
        "question": "Does the paper provide reasons for dropout or non-participation?",
        "original": "State how many participants dropped out/declined participation and the reason(s) given OR provide response rate OR state that no participants dropped out/declined participation.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "5.3",
        "category": "Non-participation",
        "question": "Does the paper provide the response rate or explicitly state that no participants dropped out or declined participation?",
        "original": "State how many participants dropped out/declined participation and the reason(s) given OR provide response rate OR state that no participants dropped out/declined participation.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "6.1",
        "category": "Sampling strategy",
        "question": "Does the paper describe the sampling procedure (e.g. random, snowball, stratified, convenience)?",
        "original": "Describe the sampling procedure (e.g. random, snowball, stratified, convenience). Describe the statistical methods that were used to predetermine sample size OR if no sample-size calculation was performed, describe how sample sizes were chosen and provide a rationale for why these sample sizes are sufficient. For qualitative data, please indicate whether data saturation was considered, and what criteria were used to decide that no further sampling was needed.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "6.2",
        "category": "Sampling strategy",
        "question": "Does the paper describe the statistical methods used to predetermine sample size?",
        "original": "Describe the sampling procedure (e.g. random, snowball, stratified, convenience). Describe the statistical methods that were used to predetermine sample size OR if no sample-size calculation was performed, describe how sample sizes were chosen and provide a rationale for why these sample sizes are sufficient. For qualitative data, please indicate whether data saturation was considered, and what criteria were used to decide that no further sampling was needed.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "6.3",
        "category": "Sampling strategy",
        "question": "If no sample-size calculation was performed, does the paper explain how sample sizes were chosen and provide a rationale for why these sample sizes are sufficient?",
        "original": "Describe the sampling procedure (e.g. random, snowball, stratified, convenience). Describe the statistical methods that were used to predetermine sample size OR if no sample-size calculation was performed, describe how sample sizes were chosen and provide a rationale for why these sample sizes are sufficient. For qualitative data, please indicate whether data saturation was considered, and what criteria were used to decide that no further sampling was needed.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "6.4",
        "category": "Sampling strategy",
        "question": "For qualitative data, does the paper indicate whether data saturation was considered and describe the criteria used to decide that no further sampling was needed?",
        "original": "Describe the sampling procedure (e.g. random, snowball, stratified, convenience). Describe the statistical methods that were used to predetermine sample size OR if no sample-size calculation was performed, describe how sample sizes were chosen and provide a rationale for why these sample sizes are sufficient. For qualitative data, please indicate whether data saturation was considered, and what criteria were used to decide that no further sampling was needed.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "7.1",
        "category": "Data exclusions",
        "question": "Does the paper state whether any data were excluded from the analyses?",
        "original": "State whether any data were excluded from the analyses. If so, state the precise number of exclusions and the rationale behind them, indicating whether exclusion criteria were pre-established.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "7.2",
        "category": "Data exclusions",
        "question": "If data were excluded, does the paper provide the exact number of exclusions and the rationale behind them?",
        "original": "If no data were excluded from the analyses, state so OR if data were excluded, provide the exact number of exclusions and the rationale behind them, indicating whether exclusion criteria were pre-established.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "7.3",
        "category": "Data exclusions",
        "question": "Does the paper indicate whether exclusion criteria were pre-established?",
        "original": "If no data were excluded from the analyses, state so OR if data were excluded, provide the exact number of exclusions and the rationale behind them, indicating whether exclusion criteria were pre-established.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "8.1",
        "category": "Research sample",
        "question": "Does the paper state the research sample (e.g. Harvard university undergraduates, villagers in rural India)?",
        "original": "State the research sample (e.g. Harvard university undergraduates, villagers in rural India) and provide relevant demographic information (e.g. age, sex) and indicate whether the sample is representative. Provide a rationale for the study sample chosen. For studies involving existing datasets, please describe the dataset and source.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "8.2",
        "category": "Research sample",
        "question": "Does the paper provide relevant demographic information (e.g. age, sex) and indicate whether the sample is representative?",
        "original": "State the research sample (e.g. Harvard university undergraduates, villagers in rural India) and provide relevant demographic information (e.g. age, sex) and indicate whether the sample is representative. Provide a rationale for the study sample chosen. For studies involving existing datasets, please describe the dataset and source.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "8.3",
        "category": "Research sample",
        "question": "Does the paper provide a rationale for the study sample chosen?",
        "original": "State the research sample (e.g. Harvard university undergraduates, villagers in rural India) and provide relevant demographic information (e.g. age, sex) and indicate whether the sample is representative. Provide a rationale for the study sample chosen. For studies involving existing datasets, please describe the dataset and source.",
        "section": "Behavioral/social sciences study design"
    },
    {
        "item_id": "8.4",
        "category": "Research sample",
        "question": "For studies using existing datasets, does the paper describe the dataset and its source?",
        "original": "State the research sample (e.g. Harvard university undergraduates, villagers in rural India) and provide relevant demographic information (e.g. age, sex) and indicate whether the sample is representative. Provide a rationale for the study sample chosen. For studies involving existing datasets, please describe the dataset and source.",
        "section": "Behavioral/social sciences study design"
    }
]

def main():
    """Initialize the database with checklist items."""
    # Load environment variables
    load_dotenv()
    
    # Initialize database service
    db_service = DatabaseService(os.getenv("MONGODB_URI"))
    
    print("Initializing database...")
    
    # Clear existing checklist items
    db_service.checklist_items.delete_many({})
    
    # Insert new checklist items
    for item in CHECKLIST_ITEMS:
        # Convert item_id to string to ensure consistent format
        item["item_id"] = str(item["item_id"])
        db_service.checklist_items.insert_one(item)
    
    print(f"Successfully initialized {len(CHECKLIST_ITEMS)} checklist items in the database")

if __name__ == "__main__":
    main()
