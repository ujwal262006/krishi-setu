"""
Krishi Setu — Seed Data
Real Indian government agricultural schemes with structured eligibility criteria.
Run with: python -m app.seed
"""

import hashlib
import sys
from datetime import datetime

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.models import Ministry, Scheme, Source, SourceFormat


def get_slug(name: str) -> str:
    return name.lower().replace(" ", "-").replace("/", "-").replace(",", "").replace("(", "").replace(")", "")


def seed_ministries(db: Session) -> dict[str, int]:
    ministries_data = [
        {
            "name": "Ministry of Agriculture and Farmers Welfare",
            "name_hindi": "कृषि एवं किसान कल्याण मंत्रालय",
            "acronym": "MoAFW",
            "website_url": "https://agricoop.nic.in",
        },
        {
            "name": "Ministry of Finance",
            "name_hindi": "वित्त मंत्रालय",
            "acronym": "MoF",
            "website_url": "https://finmin.nic.in",
        },
        {
            "name": "Ministry of Jal Shakti",
            "name_hindi": "जल शक्ति मंत्रालय",
            "acronym": "MoJS",
            "website_url": "https://jalshakti-dowr.gov.in",
        },
        {
            "name": "Ministry of Rural Development",
            "name_hindi": "ग्रामीण विकास मंत्रालय",
            "acronym": "MoRD",
            "website_url": "https://rural.nic.in",
        },
        {
            "name": "Small Farmers Agribusiness Consortium",
            "name_hindi": "लघु कृषक कृषि व्यापार संघ",
            "acronym": "SFAC",
            "website_url": "https://www.sfacindia.com",
        },
    ]

    ministry_ids: dict[str, int] = {}
    for data in ministries_data:
        existing = db.query(Ministry).filter(Ministry.name == data["name"]).first()
        if existing:
            ministry_ids[data["acronym"]] = existing.id
            print(f"  [skip] Ministry already exists: {data['name']}")
            continue
        ministry = Ministry(**data)
        db.add(ministry)
        db.flush()
        ministry_ids[data["acronym"]] = ministry.id
        print(f"  [+] Ministry: {data['name']}")

    db.commit()
    return ministry_ids


def seed_sources(db: Session, ministry_ids: dict[str, int]) -> None:
    sources_data = [
        {
            "name": "PM-KISAN Official Portal",
            "base_url": "https://pmkisan.gov.in",
            "format": SourceFormat.HTML,
            "ministry_id": ministry_ids.get("MoAFW"),
            "crawl_interval_hours": 24,
            "max_depth": 3,
            "rate_limit_rps": 1.0,
        },
        {
            "name": "Agriculture Ministry Schemes Portal",
            "base_url": "https://agricoop.nic.in/en/schemes",
            "format": SourceFormat.HTML,
            "ministry_id": ministry_ids.get("MoAFW"),
            "crawl_interval_hours": 48,
            "max_depth": 4,
            "rate_limit_rps": 0.5,
        },
        {
            "name": "PMFBY Portal",
            "base_url": "https://pmfby.gov.in",
            "format": SourceFormat.HTML,
            "ministry_id": ministry_ids.get("MoAFW"),
            "crawl_interval_hours": 24,
            "max_depth": 3,
            "rate_limit_rps": 1.0,
        },
        {
            "name": "Rural Development Ministry",
            "base_url": "https://rural.nic.in",
            "format": SourceFormat.HTML,
            "ministry_id": ministry_ids.get("MoRD"),
            "crawl_interval_hours": 48,
            "max_depth": 3,
            "rate_limit_rps": 1.0,
        },
        {
            "name": "Jal Jeevan Mission Portal",
            "base_url": "https://jaljeevanmission.gov.in",
            "format": SourceFormat.HTML,
            "ministry_id": ministry_ids.get("MoJS"),
            "crawl_interval_hours": 72,
            "max_depth": 2,
            "rate_limit_rps": 1.0,
        },
    ]

    for data in sources_data:
        existing = db.query(Source).filter(Source.base_url == data["base_url"]).first()
        if existing:
            print(f"  [skip] Source already exists: {data['base_url']}")
            continue
        source = Source(**data)
        db.add(source)
        print(f"  [+] Source: {data['name']}")

    db.commit()


def seed_schemes(db: Session, ministry_ids: dict[str, int]) -> None:
    schemes_data = [
        {
            "name": "PM Kisan Samman Nidhi (PM-KISAN)",
            "name_hindi": "प्रधानमंत्री किसान सम्मान निधि",
            "slug": "pm-kisan-samman-nidhi",
            "description": (
                "Direct income support of ₹6,000 per year to small and marginal farmers, "
                "paid in three equal installments of ₹2,000 directly into bank accounts."
            ),
            "ministry_id": ministry_ids.get("MoAFW"),
            "eligibility_criteria": {
                "land_holding_acres": {"max": 5},
                "land_ownership": "required",
                "citizenship": "Indian",
                "excluded": [
                    "institutional_land_holders",
                    "constitutional_post_holders",
                    "serving_retired_govt_employees",
                    "income_tax_payers",
                    "professionals_doctors_engineers_lawyers",
                ],
            },
            "benefits": {
                "amount_inr": 6000,
                "frequency": "annual",
                "installments": 3,
                "installment_amount": 2000,
                "mode": "DBT",
            },
            "application_url": "https://pmkisan.gov.in",
            "source_url": "https://pmkisan.gov.in/home.aspx",
            "search_synonyms": [
                "pm kisan", "kisan samman nidhi", "6000 rupee scheme",
                "किसान सम्मान", "direct benefit transfer farmer",
                "small farmer income support", "kisan nidhi",
            ],
        },
        {
            "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
            "name_hindi": "प्रधानमंत्री फसल बीमा योजना",
            "slug": "pradhan-mantri-fasal-bima-yojana",
            "description": (
                "Comprehensive crop insurance scheme providing financial support to farmers "
                "suffering crop loss or damage due to unforeseen calamities like natural fires, "
                "lightning, storm, hailstorm, cyclone, typhoon, flood, etc."
            ),
            "ministry_id": ministry_ids.get("MoAFW"),
            "eligibility_criteria": {
                "citizenship": "Indian",
                "occupation": "farmer",
                "crop_sown": "required",
                "land_holding_acres": {"min": 0.1},
                "states": ["all"],
            },
            "benefits": {
                "premium_rate_kharif": "2%",
                "premium_rate_rabi": "1.5%",
                "premium_rate_horticulture": "5%",
                "coverage": "full_sum_insured",
                "mode": "DBT",
            },
            "application_url": "https://pmfby.gov.in",
            "source_url": "https://pmfby.gov.in",
            "search_synonyms": [
                "fasal bima", "crop insurance", "फसल बीमा", "pmfby",
                "natural disaster crop loss", "kharif insurance", "rabi insurance",
                "bima yojana", "फसल नुकसान",
            ],
        },
        {
            "name": "Sub-Mission on Agricultural Mechanization (SMAM)",
            "name_hindi": "कृषि यंत्रीकरण पर उप-मिशन",
            "slug": "sub-mission-agricultural-mechanization-smam",
            "description": (
                "Provides financial assistance to farmers for purchase of agricultural machinery "
                "and equipment. Subsidy ranges from 40% to 50% for general category and up to "
                "80% for SC/ST farmers."
            ),
            "ministry_id": ministry_ids.get("MoAFW"),
            "eligibility_criteria": {
                "citizenship": "Indian",
                "occupation": "farmer",
                "land_holding_acres": {"max": 10},
                "subsidy_rates": {
                    "general": 0.40,
                    "sc_st": 0.80,
                    "women": 0.50,
                    "small_marginal": 0.50,
                },
            },
            "benefits": {
                "subsidy_general_percent": 40,
                "subsidy_sc_st_percent": 80,
                "subsidy_women_percent": 50,
                "covered_equipment": [
                    "tractor", "power tiller", "harvester", "thresher",
                    "seed drill", "sprayer", "rotavator",
                ],
            },
            "application_url": "https://agrimachinery.nic.in",
            "source_url": "https://agricoop.nic.in/en/smam",
            "search_synonyms": [
                "smam", "tractor subsidy", "tractor ke liye paisa",
                "कृषि यंत्र", "farm equipment subsidy", "harvester subsidy",
                "agricultural machinery scheme", "yantrikaran",
                "tractor loan subsidy", "कृषि मशीनरी",
            ],
        },
        {
            "name": "Pradhan Mantri Krishi Sinchai Yojana (PMKSY)",
            "name_hindi": "प्रधानमंत्री कृषि सिंचाई योजना",
            "slug": "pradhan-mantri-krishi-sinchai-yojana",
            "description": (
                "Aims to enhance water use efficiency and expand cultivable area under irrigation "
                "with the motto 'Har Khet Ko Pani, More Crop Per Drop'. Includes drip and "
                "sprinkler irrigation subsidies."
            ),
            "ministry_id": ministry_ids.get("MoAFW"),
            "eligibility_criteria": {
                "citizenship": "Indian",
                "occupation": "farmer",
                "land_holding_acres": {"min": 0.1},
                "irrigation_type": ["drip", "sprinkler", "micro_irrigation"],
            },
            "benefits": {
                "subsidy_small_marginal_percent": 55,
                "subsidy_other_percent": 45,
                "covered": ["drip_irrigation", "sprinkler_system", "micro_irrigation"],
            },
            "application_url": "https://pmksy.gov.in",
            "source_url": "https://pmksy.gov.in",
            "search_synonyms": [
                "pmksy", "drip irrigation subsidy", "sinchai yojana",
                "सिंचाई योजना", "sprinkler subsidy", "har khet ko pani",
                "irrigation scheme", "drip subsidy", "टपक सिंचाई",
            ],
        },
        {
            "name": "Soil Health Card Scheme",
            "name_hindi": "मृदा स्वास्थ्य कार्ड योजना",
            "slug": "soil-health-card-scheme",
            "description": (
                "Provides soil health cards to farmers which carry crop-wise recommendations "
                "of nutrients and fertilizers required for individual farms to help farmers "
                "improve productivity through judicious use of inputs."
            ),
            "ministry_id": ministry_ids.get("MoAFW"),
            "eligibility_criteria": {
                "citizenship": "Indian",
                "occupation": "farmer",
                "land_ownership": "required",
            },
            "benefits": {
                "card_type": "Soil Health Card",
                "testing_frequency": "every_2_years",
                "parameters_tested": 12,
                "cost_to_farmer": 0,
            },
            "application_url": "https://soilhealth.dac.gov.in",
            "source_url": "https://soilhealth.dac.gov.in",
            "search_synonyms": [
                "soil health card", "मृदा स्वास्थ्य कार्ड", "soil testing",
                "mitti ki janch", "soil card", "fertilizer recommendation",
                "मिट्टी परीक्षण", "krishi card",
            ],
        },
        {
            "name": "National Agriculture Market (eNAM)",
            "name_hindi": "राष्ट्रीय कृषि बाजार",
            "slug": "national-agriculture-market-enam",
            "description": (
                "Pan-India electronic trading portal networking existing APMC mandis to create "
                "a unified national market for agricultural commodities. Enables farmers to get "
                "better prices through online bidding."
            ),
            "ministry_id": ministry_ids.get("MoAFW"),
            "eligibility_criteria": {
                "citizenship": "Indian",
                "occupation": "farmer",
                "bank_account": "required",
                "aadhaar": "required",
            },
            "benefits": {
                "platform": "online_mandi",
                "transparent_pricing": True,
                "direct_payment": True,
                "commodities_covered": "150+",
            },
            "application_url": "https://enam.gov.in",
            "source_url": "https://enam.gov.in",
            "search_synonyms": [
                "enam", "e-nam", "online mandi", "राष्ट्रीय कृषि बाजार",
                "digital mandi", "sell crop online", "mandi portal",
                "फसल बेचना", "better price crop",
            ],
        },
        {
            "name": "Kisan Credit Card (KCC)",
            "name_hindi": "किसान क्रेडिट कार्ड",
            "slug": "kisan-credit-card",
            "description": (
                "Provides adequate and timely credit to farmers for their agricultural operations, "
                "maintenance of farm assets, and allied activities at subsidized interest rates. "
                "Credit limit based on landholding and crops grown."
            ),
            "ministry_id": ministry_ids.get("MoF"),
            "eligibility_criteria": {
                "citizenship": "Indian",
                "occupation": ["farmer", "fisherman", "animal_husbandry"],
                "age": {"min": 18, "max": 75},
                "land_ownership_or_lease": "required",
            },
            "benefits": {
                "interest_rate_percent": 4,
                "interest_subvention_percent": 3,
                "credit_limit_base_inr": 300000,
                "repayment_period_months": 12,
                "insurance_coverage": True,
            },
            "application_url": "https://www.nabard.org/content1.aspx?id=572",
            "source_url": "https://www.nabard.org/content1.aspx?id=572",
            "search_synonyms": [
                "kcc", "kisan credit card", "किसान क्रेडिट कार्ड",
                "kisan loan", "4% interest loan", "farm credit card",
                "kisan card", "krishi loan", "short term credit farmer",
            ],
        },
        {
            "name": "Pradhan Mantri Kisan MaanDhan Yojana (PM-KMY)",
            "name_hindi": "प्रधानमंत्री किसान मानधन योजना",
            "slug": "pradhan-mantri-kisan-maandhan-yojana",
            "description": (
                "Voluntary and contributory pension scheme for small and marginal farmers. "
                "Provides ₹3,000 per month pension after age 60. Government contributes "
                "equal amount as the farmer."
            ),
            "ministry_id": ministry_ids.get("MoAFW"),
            "eligibility_criteria": {
                "age": {"min": 18, "max": 40},
                "land_holding_acres": {"max": 5},
                "citizenship": "Indian",
                "excluded": ["income_tax_payers", "EPFO_ESIC_NPS_members"],
            },
            "benefits": {
                "pension_amount_inr": 3000,
                "pension_frequency": "monthly",
                "government_contribution": "equal_to_farmer",
                "eligibility_age": 60,
            },
            "application_url": "https://maandhan.in",
            "source_url": "https://maandhan.in/pmkmy",
            "search_synonyms": [
                "pm kmy", "kisan pension", "किसान पेंशन", "maandhan yojana",
                "farmer pension scheme", "3000 pension", "old age pension farmer",
                "kisan maandhan", "pension yojana kisan",
            ],
        },
        {
            "name": "Paramparagat Krishi Vikas Yojana (PKVY)",
            "name_hindi": "परंपरागत कृषि विकास योजना",
            "slug": "paramparagat-krishi-vikas-yojana",
            "description": (
                "Promotes organic farming through cluster approach. Provides financial assistance "
                "of ₹50,000 per hectare for 3 years to farmers adopting organic farming methods. "
                "Focuses on soil health improvement and chemical-free production."
            ),
            "ministry_id": ministry_ids.get("MoAFW"),
            "eligibility_criteria": {
                "citizenship": "Indian",
                "occupation": "farmer",
                "cluster_size_hectares": {"min": 20},
                "commitment": "3_years_organic",
            },
            "benefits": {
                "financial_assistance_per_hectare_inr": 50000,
                "duration_years": 3,
                "annual_assistance_inr": 16500,
                "certification_support": True,
                "market_linkage": True,
            },
            "application_url": "https://agricoop.nic.in/en/pkvy",
            "source_url": "https://agricoop.nic.in/en/pkvy",
            "search_synonyms": [
                "pkvy", "organic farming scheme", "jaivik kheti",
                "परंपरागत कृषि", "organic subsidy", "chemical free farming",
                "jeevamrit", "natural farming scheme", "organic certification",
            ],
        },
        {
            "name": "National Food Security Mission (NFSM)",
            "name_hindi": "राष्ट्रीय खाद्य सुरक्षा मिशन",
            "slug": "national-food-security-mission",
            "description": (
                "Aims to increase production of rice, wheat, pulses, coarse cereals and nutri-cereals "
                "through area expansion and productivity enhancement. Provides subsidized seeds, "
                "farm inputs, and training to farmers."
            ),
            "ministry_id": ministry_ids.get("MoAFW"),
            "eligibility_criteria": {
                "citizenship": "Indian",
                "occupation": "farmer",
                "crops": ["rice", "wheat", "pulses", "coarse_cereals"],
                "states": ["all"],
            },
            "benefits": {
                "subsidized_seeds": True,
                "farm_inputs_subsidy": True,
                "training_support": True,
                "demonstration_plots": True,
                "crop_coverage": ["rice", "wheat", "pulses", "maize", "barley"],
            },
            "application_url": "https://nfsm.gov.in",
            "source_url": "https://nfsm.gov.in",
            "search_synonyms": [
                "nfsm", "food security mission", "खाद्य सुरक्षा",
                "subsidized seeds", "beej subsidy", "wheat scheme",
                "pulses scheme", "dal subsidy", "rice farming scheme",
            ],
        },
        {
            "name": "Rashtriya Krishi Vikas Yojana (RKVY)",
            "name_hindi": "राष्ट्रीय कृषि विकास योजना",
            "slug": "rashtriya-krishi-vikas-yojana",
            "description": (
                "Provides states flexibility and autonomy in planning and executing agricultural "
                "development programmes. Funds agricultural infrastructure, processing, and "
                "modernization of agriculture."
            ),
            "ministry_id": ministry_ids.get("MoAFW"),
            "eligibility_criteria": {
                "citizenship": "Indian",
                "occupation": ["farmer", "fpo", "agri_entrepreneur"],
                "states": ["all"],
                "project_based": True,
            },
            "benefits": {
                "grant_type": "state_channeled",
                "infrastructure_support": True,
                "agro_processing_support": True,
                "startup_support": True,
            },
            "application_url": "https://rkvy.nic.in",
            "source_url": "https://rkvy.nic.in",
            "search_synonyms": [
                "rkvy", "rashtriya krishi vikas", "कृषि विकास योजना",
                "agriculture infrastructure", "agri grant", "krishi vikas",
            ],
        },
        {
            "name": "PM Kisan FPO Scheme",
            "name_hindi": "किसान उत्पादक संगठन योजना",
            "slug": "pm-kisan-fpo-scheme",
            "description": (
                "Promotes formation of Farmer Producer Organizations (FPOs) to help farmers "
                "get better prices, credit, technology and market access. Provides financial "
                "assistance of ₹15 lakh to each FPO over 3 years."
            ),
            "ministry_id": ministry_ids.get("MoAFW"),
            "eligibility_criteria": {
                "entity_type": "FPO",
                "minimum_members": 300,
                "plain_area_members": 300,
                "hilly_area_members": 100,
                "registration": "required",
            },
            "benefits": {
                "financial_assistance_inr": 1500000,
                "duration_years": 3,
                "credit_guarantee": True,
                "equity_grant": True,
                "market_linkage": True,
            },
            "application_url": "https://sfacindia.com",
            "source_url": "https://sfacindia.com",
            "search_synonyms": [
                "fpo scheme", "farmer producer organization",
                "किसान संगठन", "kisan group scheme", "fpo grant",
                "collective farming", "farmer cooperative",
            ],
        },
        {
            "name": "Agriculture Infrastructure Fund (AIF)",
            "name_hindi": "कृषि अवसंरचना कोष",
            "slug": "agriculture-infrastructure-fund",
            "description": (
                "Provides medium to long-term debt financing for investment in viable projects "
                "for post-harvest management infrastructure and community farming assets. "
                "Interest subvention of 3% per annum for loans up to ₹2 crore."
            ),
            "ministry_id": ministry_ids.get("MoAFW"),
            "eligibility_criteria": {
                "entity_type": ["farmer", "fpo", "agri_entrepreneur", "startup", "cooperative"],
                "project_type": ["cold_storage", "warehouse", "processing_unit", "sorting_grading"],
                "loan_amount_max_inr": 20000000,
            },
            "benefits": {
                "interest_subvention_percent": 3,
                "credit_guarantee": True,
                "moratorium_period_years": 2,
                "repayment_period_years": 7,
                "total_fund_crore": 100000,
            },
            "application_url": "https://agriinfra.dac.gov.in",
            "source_url": "https://agriinfra.dac.gov.in",
            "search_synonyms": [
                "aif", "agriculture infrastructure fund", "cold storage subsidy",
                "warehouse scheme", "post harvest infrastructure",
                "kisan cold storage", "godown subsidy", "processing unit loan",
            ],
        },
        {
            "name": "Pradhan Mantri Annadata Aay SanraksHan Abhiyan (PM-AASHA)",
            "name_hindi": "प्रधानमंत्री अन्नदाता आय संरक्षण अभियान",
            "slug": "pradhan-mantri-annadata-aay-sanrakshan-abhiyan",
            "description": (
                "Ensures farmers get MSP (Minimum Support Price) for their produce. Includes "
                "Price Support Scheme (PSS), Price Deficiency Payment Scheme (PDPS), and "
                "Private Procurement and Stockist Scheme (PPSS)."
            ),
            "ministry_id": ministry_ids.get("MoAFW"),
            "eligibility_criteria": {
                "citizenship": "Indian",
                "occupation": "farmer",
                "crops": ["oilseeds", "pulses", "copra"],
                "registration": "required",
            },
            "benefits": {
                "msp_guarantee": True,
                "price_deficiency_payment": True,
                "private_procurement_option": True,
            },
            "application_url": "https://agricoop.nic.in",
            "source_url": "https://agricoop.nic.in/en/pm-aasha",
            "search_synonyms": [
                "pm aasha", "msp scheme", "minimum support price",
                "न्यूनतम समर्थन मूल्य", "annadata yojana",
                "price support scheme", "oilseed msp", "pulses msp",
            ],
        },
        {
            "name": "Gramin Bhandaran Yojana (Rural Godown Scheme)",
            "name_hindi": "ग्रामीण भंडारण योजना",
            "slug": "gramin-bhandaran-yojana",
            "description": (
                "Creates scientific storage capacity in rural areas to reduce post-harvest losses "
                "and enable farmers to store their produce and sell when prices are favorable. "
                "Subsidy of 25% to 33.33% on construction cost."
            ),
            "ministry_id": ministry_ids.get("MoAFW"),
            "eligibility_criteria": {
                "entity_type": ["farmer", "cooperative", "fpo", "gram_panchayat"],
                "storage_capacity_tonnes": {"min": 100, "max": 30000},
                "location": "rural",
            },
            "benefits": {
                "subsidy_general_percent": 25,
                "subsidy_sc_st_percent": 33.33,
                "subsidy_northeast_percent": 33.33,
                "nabard_refinance": True,
            },
            "application_url": "https://www.nabard.org",
            "source_url": "https://agricoop.nic.in/en/godown-scheme",
            "search_synonyms": [
                "godown scheme", "rural storage subsidy", "bhandaran yojana",
                "ग्रामीण भंडारण", "warehouse subsidy rural", "storage facility farmer",
                "grain storage scheme", "anaj godown",
            ],
        },
        {
            "name": "National Horticulture Mission (NHM)",
            "name_hindi": "राष्ट्रीय बागवानी मिशन",
            "slug": "national-horticulture-mission",
            "description": (
                "Promotes holistic growth of the horticulture sector covering fruits, vegetables, "
                "root and tuber crops, mushroom, spices, flowers, aromatic plants, coconut, "
                "cashew and cocoa. Subsidies for planting material, infrastructure, and processing."
            ),
            "ministry_id": ministry_ids.get("MoAFW"),
            "eligibility_criteria": {
                "citizenship": "Indian",
                "occupation": "farmer",
                "crop_type": ["fruits", "vegetables", "spices", "flowers", "medicinal_plants"],
            },
            "benefits": {
                "planting_material_subsidy": True,
                "drip_irrigation_subsidy": True,
                "cold_storage_subsidy": True,
                "processing_unit_subsidy": True,
                "subsidy_range_percent": "25-50",
            },
            "application_url": "https://nhb.gov.in",
            "source_url": "https://nhb.gov.in",
            "search_synonyms": [
                "nhm", "horticulture mission", "sabzi subsidy", "फल सब्जी योजना",
                "vegetable farming scheme", "fruit farming subsidy",
                "bagwani yojana", "flower farming scheme", "spice farming",
            ],
        },
        {
            "name": "PM SVANidhi (Micro Credit for Street Vendors)",
            "name_hindi": "पीएम स्वनिधि",
            "slug": "pm-svanidhi",
            "description": (
                "Provides affordable working capital loan of ₹10,000 initially to street vendors "
                "to resume their businesses post COVID-19. Includes vendors selling vegetables, "
                "fruits, and agricultural produce."
            ),
            "ministry_id": ministry_ids.get("MoRD"),
            "eligibility_criteria": {
                "occupation": "street_vendor",
                "includes": ["vegetable_vendor", "fruit_vendor", "agri_produce_vendor"],
                "vending_certificate": "required",
                "citizenship": "Indian",
            },
            "benefits": {
                "initial_loan_inr": 10000,
                "second_loan_inr": 20000,
                "third_loan_inr": 50000,
                "interest_subsidy_percent": 7,
                "digital_transaction_incentive": True,
            },
            "application_url": "https://pmsvanidhi.mohua.gov.in",
            "source_url": "https://pmsvanidhi.mohua.gov.in",
            "search_synonyms": [
                "svanidhi", "street vendor loan", "rehri wala loan",
                "sabzi wala loan", "vendor loan scheme", "10000 loan scheme",
                "फेरी वाला लोन", "hawker loan",
            ],
        },
        {
            "name": "National Rural Livelihood Mission (NRLM / Aajeevika)",
            "name_hindi": "राष्ट्रीय ग्रामीण आजीविका मिशन",
            "slug": "national-rural-livelihood-mission",
            "description": (
                "Reduces poverty by enabling poor households to access gainful self-employment "
                "and skilled wage employment. Provides interest subvention on SHG loans, "
                "revolving funds, and community investment funds."
            ),
            "ministry_id": ministry_ids.get("MoRD"),
            "eligibility_criteria": {
                "citizenship": "Indian",
                "gender": "female",
                "shg_member": "required",
                "bpl_preferred": True,
                "rural": True,
            },
            "benefits": {
                "revolving_fund_inr": 15000,
                "community_investment_fund_inr": 250000,
                "interest_subvention_percent": 7,
                "bank_linkage": True,
            },
            "application_url": "https://aajeevika.gov.in",
            "source_url": "https://aajeevika.gov.in",
            "search_synonyms": [
                "nrlm", "aajeevika", "shg loan", "self help group",
                "महिला समूह लोन", "rural women scheme", "swayam sahayata samuh",
                "women livelihood scheme", "rural livelihood",
            ],
        },
        {
            "name": "Pradhan Mantri Awas Yojana Gramin (PMAY-G)",
            "name_hindi": "प्रधानमंत्री आवास योजना ग्रामीण",
            "slug": "pradhan-mantri-awas-yojana-gramin",
            "description": (
                "Provides financial assistance to rural BPL households for construction of "
                "pucca houses. Assistance of ₹1.20 lakh in plains and ₹1.30 lakh in hilly/difficult areas."
            ),
            "ministry_id": ministry_ids.get("MoRD"),
            "eligibility_criteria": {
                "citizenship": "Indian",
                "location": "rural",
                "is_bpl": True,
                "housing_status": "no_pucca_house",
                "excluded": ["income_tax_payers", "motorized_vehicle_owners", "refrigerator_owners"],
            },
            "benefits": {
                "assistance_plains_inr": 120000,
                "assistance_hilly_inr": 130000,
                "additional_toilet_inr": 12000,
                "bank_loan_linkage": True,
            },
            "application_url": "https://pmayg.nic.in",
            "source_url": "https://pmayg.nic.in",
            "search_synonyms": [
                "pmay gramin", "rural housing scheme", "pucca ghar yojana",
                "gramin awas", "गृह निर्माण योजना", "bpl housing",
                "awas yojana", "rural house subsidy",
            ],
        },
        {
            "name": "Mahatma Gandhi NREGA (MGNREGS)",
            "name_hindi": "महात्मा गांधी राष्ट्रीय ग्रामीण रोजगार गारंटी योजना",
            "slug": "mahatma-gandhi-nrega",
            "description": (
                "Provides at least 100 days of guaranteed wage employment in a financial year "
                "to every rural household whose adult members volunteer to do unskilled manual work. "
                "Wage rate varies by state."
            ),
            "ministry_id": ministry_ids.get("MoRD"),
            "eligibility_criteria": {
                "citizenship": "Indian",
                "location": "rural",
                "age": {"min": 18},
                "willingness": "unskilled_manual_work",
                "job_card": "required",
            },
            "benefits": {
                "guaranteed_days": 100,
                "additional_days_drought": 50,
                "wage_mode": "DBT",
                "payment_within_days": 15,
            },
            "application_url": "https://nrega.nic.in",
            "source_url": "https://nrega.nic.in",
            "search_synonyms": [
                "mgnrega", "nrega", "100 days work scheme", "job card scheme",
                "रोजगार गारंटी", "nregs", "manrega", "daily wage rural",
                "mazdoori yojana", "rural employment guarantee",
            ],
        },
        {
            "name": "Jal Jeevan Mission (JJM)",
            "name_hindi": "जल जीवन मिशन",
            "slug": "jal-jeevan-mission",
            "description": (
                "Aims to provide safe and adequate drinking water through individual household "
                "tap connections to all households in rural India by 2024. "
                "Functional Household Tap Connection (FHTC) to every rural home."
            ),
            "ministry_id": ministry_ids.get("MoJS"),
            "eligibility_criteria": {
                "citizenship": "Indian",
                "location": "rural",
                "housing_status": "rural_household",
            },
            "benefits": {
                "tap_connection": "free",
                "water_supply_lpcd": 55,
                "connection_type": "FHTC",
                "target": "every_rural_household",
            },
            "application_url": "https://jaljeevanmission.gov.in",
            "source_url": "https://jaljeevanmission.gov.in",
            "search_keywords": [
                "jal jeevan mission", "tap water scheme", "nal se jal",
                "नल जल योजना", "rural water supply", "household tap connection",
                "pani connection yojana", "JJM",
            ],
        },
    ]

    for data in schemes_data:
        existing = db.query(Scheme).filter(Scheme.slug == data["slug"]).first()
        if existing:
            print(f"  [skip] Scheme already exists: {data['name'][:50]}")
            continue

        # Generate URL hash for duplicate detection
        url_hash = None
        if data.get("source_url"):
            url_hash = hashlib.sha256(data["source_url"].encode()).hexdigest()

        scheme = Scheme(
            name=data["name"],
            name_hindi=data.get("name_hindi"),
            slug=data["slug"],
            description=data.get("description"),
            ministry_id=data.get("ministry_id"),
            eligibility_criteria=data.get("eligibility_criteria", {}),
            benefits=data.get("benefits", {}),
            application_url=data.get("application_url"),
            source_url=data.get("source_url"),
            search_synonyms=data.get("search_synonyms", []),
            url_hash=url_hash,
            is_active=True,
        )
        db.add(scheme)
        print(f"  [+] Scheme: {data['name'][:60]}")

    db.commit()


def main() -> None:
    print("=== Krishi Setu Seed Script ===\n")
    db = SessionLocal()
    try:
        print("[1/3] Seeding ministries...")
        ministry_ids = seed_ministries(db)

        print("\n[2/3] Seeding sources...")
        seed_sources(db, ministry_ids)

        print("\n[3/3] Seeding schemes...")
        seed_schemes(db, ministry_ids)

        print("\n=== Seed complete ===")
        scheme_count = db.query(Scheme).count()
        ministry_count = db.query(Ministry).count()
        source_count = db.query(Source).count()
        print(f"  Ministries: {ministry_count}")
        print(f"  Sources:    {source_count}")
        print(f"  Schemes:    {scheme_count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
