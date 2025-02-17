"""Script to initialize checklist items in the database."""
from app.services.db_service import DatabaseService
import os
from datetime import datetime, timezone

# Initial checklist items data
CHECKLIST_ITEMS = [
    {
        "item_id": "1.1",
        "category": "Data collection",
        "question": "Does the paper provide details about the data collection procedure, including the instruments or devices used to record the data?",
        "description": "Look for specific mentions of data collection tools and methods, such as pen and paper, computer software, eye trackers, video/audio equipment, etc.",
        "original": "Provide details about the data collection procedure, including the instruments or devices used to record the data (e.g. pen and paper, computer, eye tracker, video or audio equipment) whether anyone was present besides the participant(s) and the researcher, and whether the researcher was blind to experimental condition and/or the study hypothesis during data collection.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "1.2",
        "category": "Data collection",
        "question": "Does the paper specify whether anyone other than the participant(s) and the researcher was present during data collection?",
        "description": "Check if the paper mentions the presence of additional observers, assistants, or other individuals during data collection sessions.",
        "original": "Provide details about the data collection procedure, including the instruments or devices used to record the data (e.g. pen and paper, computer, eye tracker, video or audio equipment) whether anyone was present besides the participant(s) and the researcher, and whether the researcher was blind to experimental condition and/or the study hypothesis during data collection.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "1.3",
        "category": "Data collection",
        "question": "Does the paper state whether the researcher was blind to the experimental condition and/or the study hypothesis during data collection?",
        "description": "Look for statements about researcher blinding or masking to conditions/hypotheses to assess potential experimenter bias.",
        "original": "Provide details about the data collection procedure, including the instruments or devices used to record the data (e.g. pen and paper, computer, eye tracker, video or audio equipment) whether anyone was present besides the participant(s) and the researcher, and whether the researcher was blind to experimental condition and/or the study hypothesis during data collection.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "2.1",
        "category": "Randomization",
        "question": "Does the paper specify whether participants were allocated into experimental groups?",
        "description": "Check if the study describes how participants were assigned to different conditions or groups in the experiment.",
        "original": "If participants were not allocated into experimental groups, state so OR describe how participants were allocated to groups, and specify whether allocation was done by investigator(s), OR state that allocation was random, with method of randomization.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "2.2",
        "category": "Randomization",
        "question": "If participants were allocated into groups, does the paper state whether allocation was random?",
        "description": "Check if the study describes the method of randomization used to assign participants to groups.",
        "original": "If participants were not allocated into experimental groups, state so OR describe how participants were allocated to groups, and if allocation was not random, describe how covariates were controlled.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "2.3",
        "category": "Randomization",
        "question": "If allocation was not random, does the paper describe how covariates were controlled?",
        "description": "Check if the study describes how covariates were controlled if participants were not randomly allocated to groups.",
        "original": "If participants were not allocated into experimental groups, state so OR describe how participants were allocated to groups, and if allocation was not random, describe how covariates were controlled.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "4.1",
        "category": "Timing",
        "question": "Does the paper indicate the start and stop dates of data collection?",
        "description": "Check if the paper provides specific dates or a date range for data collection.",
        "original": "Indicate the start and stop dates of data collection. If there is a gap between collection periods, state the dates for each sample cohort.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "4.2",
        "category": "Timing",
        "question": "If there was a gap between collection periods, does the paper state the dates for each sample cohort?",
        "description": "Check if the paper provides specific dates or a date range for each sample cohort if there was a gap between collection periods.",
        "original": "Indicate the start and stop dates of data collection. If there is a gap between collection periods, state the dates for each sample cohort.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "5.1",
        "category": "Non-participation",
        "question": "Does the paper specify how many participants dropped out or declined participation?",
        "description": "Check if the paper provides a specific number of participants who dropped out or declined participation.",
        "original": "State how many participants dropped out/declined participation and the reason(s) given OR provide response rate OR state that no participants dropped out/declined participation.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "5.2",
        "category": "Non-participation",
        "question": "Does the paper provide reasons for dropout or non-participation?",
        "description": "Check if the paper provides reasons for participants dropping out or declining participation.",
        "original": "State how many participants dropped out/declined participation and the reason(s) given OR provide response rate OR state that no participants dropped out/declined participation.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "5.3",
        "category": "Non-participation",
        "question": "Does the paper provide the response rate or explicitly state that no participants dropped out or declined participation?",
        "description": "Check if the paper provides a response rate or states that no participants dropped out or declined participation.",
        "original": "State how many participants dropped out/declined participation and the reason(s) given OR provide response rate OR state that no participants dropped out/declined participation.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "6.1",
        "category": "Sampling strategy",
        "question": "Does the paper describe the sampling procedure (e.g. random, snowball, stratified, convenience)?",
        "description": "Check if the paper describes the method used to select participants for the study.",
        "original": "Describe the sampling procedure (e.g. random, snowball, stratified, convenience). Describe the statistical methods that were used to predetermine sample size OR if no sample-size calculation was performed, describe how sample sizes were chosen and provide a rationale for why these sample sizes are sufficient. For qualitative data, please indicate whether data saturation was considered, and what criteria were used to decide that no further sampling was needed.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "6.2",
        "category": "Sampling strategy",
        "question": "Does the paper describe the statistical methods used to predetermine sample size?",
        "description": "Check if the paper describes the statistical methods used to determine the sample size.",
        "original": "Describe the sampling procedure (e.g. random, snowball, stratified, convenience). Describe the statistical methods that were used to predetermine sample size OR if no sample-size calculation was performed, describe how sample sizes were chosen and provide a rationale for why these sample sizes are sufficient. For qualitative data, please indicate whether data saturation was considered, and what criteria were used to decide that no further sampling was needed.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "6.3",
        "category": "Sampling strategy",
        "question": "If no sample-size calculation was performed, does the paper explain how sample sizes were chosen and provide a rationale for why these sample sizes are sufficient?",
        "description": "Check if the paper explains how sample sizes were chosen and provides a rationale for why these sample sizes are sufficient if no sample-size calculation was performed.",
        "original": "Describe the sampling procedure (e.g. random, snowball, stratified, convenience). Describe the statistical methods that were used to predetermine sample size OR if no sample-size calculation was performed, describe how sample sizes were chosen and provide a rationale for why these sample sizes are sufficient. For qualitative data, please indicate whether data saturation was considered, and what criteria were used to decide that no further sampling was needed.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "6.4",
        "category": "Sampling strategy",
        "question": "For qualitative data, does the paper indicate whether data saturation was considered and describe the criteria used to decide that no further sampling was needed?",
        "description": "Check if the paper indicates whether data saturation was considered and describes the criteria used to decide that no further sampling was needed for qualitative data.",
        "original": "Describe the sampling procedure (e.g. random, snowball, stratified, convenience). Describe the statistical methods that were used to predetermine sample size OR if no sample-size calculation was performed, describe how sample sizes were chosen and provide a rationale for why these sample sizes are sufficient. For qualitative data, please indicate whether data saturation was considered, and what criteria were used to decide that no further sampling was needed.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "7.1",
        "category": "Data exclusions",
        "question": "Does the paper state whether any data were excluded from the analyses?",
        "description": "Check if the paper states whether any data were excluded from the analyses.",
        "original": "State whether any data were excluded from the analyses. If so, state the precise number of exclusions and the rationale behind them, indicating whether exclusion criteria were pre-established.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "7.2",
        "category": "Data exclusions",
        "question": "If data were excluded, does the paper provide the exact number of exclusions and the rationale behind them?",
        "description": "Check if the paper provides the exact number of exclusions and the rationale behind them if data were excluded.",
        "original": "If no data were excluded from the analyses, state so OR if data were excluded, provide the exact number of exclusions and the rationale behind them, indicating whether exclusion criteria were pre-established.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "7.3",
        "category": "Data exclusions",
        "question": "Does the paper indicate whether exclusion criteria were pre-established?",
        "description": "Check if the paper indicates whether exclusion criteria were pre-established.",
        "original": "If no data were excluded from the analyses, state so OR if data were excluded, provide the exact number of exclusions and the rationale behind them, indicating whether exclusion criteria were pre-established.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "8.1",
        "category": "Research sample",
        "question": "Does the paper state the research sample (e.g. Harvard university undergraduates, villagers in rural India)?",
        "description": "Check if the paper states the research sample.",
        "original": "State the research sample (e.g. Harvard university undergraduates, villagers in rural India) and provide relevant demographic information (e.g. age, sex) and indicate whether the sample is representative. Provide a rationale for the study sample chosen. For studies involving existing datasets, please describe the dataset and source.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "8.2",
        "category": "Research sample",
        "question": "Does the paper provide relevant demographic information (e.g. age, sex) and indicate whether the sample is representative?",
        "description": "Check if the paper provides relevant demographic information and indicates whether the sample is representative.",
        "original": "State the research sample (e.g. Harvard university undergraduates, villagers in rural India) and provide relevant demographic information (e.g. age, sex) and indicate whether the sample is representative. Provide a rationale for the study sample chosen. For studies involving existing datasets, please describe the dataset and source.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "8.3",
        "category": "Research sample",
        "question": "Does the paper provide a rationale for the study sample chosen?",
        "description": "Check if the paper provides a rationale for the study sample chosen.",
        "original": "State the research sample (e.g. Harvard university undergraduates, villagers in rural India) and provide relevant demographic information (e.g. age, sex) and indicate whether the sample is representative. Provide a rationale for the study sample chosen. For studies involving existing datasets, please describe the dataset and source.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "item_id": "8.4",
        "category": "Research sample",
        "question": "For studies using existing datasets, does the paper describe the dataset and its source?",
        "description": "Check if the paper describes the dataset and its source for studies using existing datasets.",
        "original": "State the research sample (e.g. Harvard university undergraduates, villagers in rural India) and provide relevant demographic information (e.g. age, sex) and indicate whether the sample is representative. Provide a rationale for the study sample chosen. For studies involving existing datasets, please describe the dataset and source.",
        "section": "Behavioral/social sciences study design",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
]

def main():
    """Initialize the database with checklist items."""
    try:
        # Get MongoDB URI from environment or Streamlit secrets
        mongodb_uri = None
        try:
            import streamlit as st
            mongodb_uri = st.secrets["mongodb"]["uri"]
        except:
            # If running directly with Python, try environment variable
            mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/manuscript_db")
        
        print(f"Using MongoDB URI: {mongodb_uri}")
        
        # Initialize database service
        db_service = DatabaseService(mongodb_uri)
        
        # First, remove all existing items
        db_service.checklist_items.delete_many({})
        
        # Insert new items
        for item in CHECKLIST_ITEMS:
            try:
                # Update timestamps to use timezone-aware UTC time
                item["created_at"] = datetime.now(timezone.utc)
                item["updated_at"] = datetime.now(timezone.utc)
                db_service.save_checklist_item(item)
                print(f"Added checklist item {item['item_id']}")
            except Exception as e:
                print(f"Error adding item {item['item_id']}: {str(e)}")
        
        print("\nChecklist items initialization complete!")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Make sure MongoDB is running and accessible")

if __name__ == "__main__":
    main()
