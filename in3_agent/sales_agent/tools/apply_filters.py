# Import necassary packages
from .extract_webshops import _extract_webshops_info
from .filters import _process_price_filter, _process_prohibted_items_filter
from .bulk_people_enrichment import _people_enrichment_bulk
from .extract_people_info import _extract_people_info

# Function to apply filter
def _lead_extraction():
    """
    Use this tool to extract lead data
    
    This function helps to get the raw lead data from apollo api and
    filter leads based on the crieteria and enrich those data.
    """

    # Call the function to filter out e-commer website
    _extract_webshops_info()

    # Call the price filter function
    price_filtered_leads = _process_price_filter()
    print("Price filtered leads:", len(price_filtered_leads))

    # Call the prohibited items filter function
    domain_list = _process_prohibted_items_filter(price_filtering_leads=price_filtered_leads)
    print("Prohibited Items filtered leads:", len(domain_list))

    # Call the People Search api by passing domain list
    leads_without_enrichment = _extract_people_info(domain_list=domain_list)

    leads_with_enrichment = _people_enrichment_bulk(lead_data_without_enrichment=leads_without_enrichment)

    return leads_with_enrichment