# Import necassary packages
import os
import json
from .fetch_people_info import _extract_people_info
from .filters import _process_price_filter, _process_prohibted_items_filter
from .people_enrichment import _people_enrichment

# Function to apply filter
def _lead_extraction():
    """
    Use this tool to extract lead data
    
    This function helps to get the raw lead data from apollo api and
    filter leads based on the crieteria and enrich those data.
    """

    # Call the function to filter out e-commer website
    _extract_people_info()

    # Call the price filter function
    price_filtered_leads = _process_price_filter()
    print("Price filtered leads:", len(price_filtered_leads))

    # Call the prohibited items filter function
    leads_without_enrichment = _process_prohibted_items_filter(price_filtering_leads=price_filtered_leads)
    print("Prohibited Items filtered leads:", len(leads_without_enrichment))
    print("Filtering option has been completed sucessfully")

    leads_with_enrichment = _people_enrichment(lead_data_without_enrichment=leads_without_enrichment)

    return leads_with_enrichment