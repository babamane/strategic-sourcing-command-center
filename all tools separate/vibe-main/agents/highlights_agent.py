"""
Highlights Agent
Agent to fetch and format highlights data for companies
"""
from tools.pricing_insights_tool import get_pricing_insights
from tools.products_features_tool import get_products_features
from tools.ai_cloud_productivity_tool import get_ai_cloud_productivity
from tools.vendor_discussion_topics_tool import get_vendor_discussion_topics
from tools.meta_synergies_tool import get_meta_synergies
from tools.meta_spend_metrics_tool import get_meta_spend_metrics


def get_pricing_insights_data(company_name: str) -> dict:
    """
    Get pricing insights for a company
    
    Args:
        company_name: Name of the company
        
    Returns:
        dict with pricing insights content
    """
    content = get_pricing_insights.invoke({"company": company_name})
    return {
        "content": content,
        "tab": "pricing_insights"
    }


def get_products_features_data(company_name: str) -> dict:
    """
    Get products and features data for a company
    
    Args:
        company_name: Name of the company
        
    Returns:
        dict with products and features content
    """
    content = get_products_features.invoke({"company": company_name})
    return {
        "content": content,
        "tab": "products_features"
    }


def get_ai_cloud_productivity_data(company_name: str) -> dict:
    """
    Get AI, cloud, and productivity data for a company
    
    Args:
        company_name: Name of the company
        
    Returns:
        dict with AI, cloud, and productivity content
    """
    content = get_ai_cloud_productivity.invoke({"company": company_name})
    return {
        "content": content,
        "tab": "ai_cloud_productivity"
    }


def get_vendor_discussion_topics_data(company_name: str) -> dict:
    """
    Get vendor discussion topics for a company
    
    Args:
        company_name: Name of the company
        
    Returns:
        dict with vendor discussion topics content
    """
    content = get_vendor_discussion_topics.invoke({"company": company_name})
    return {
        "content": content,
        "tab": "vendor_topics"
    }


def get_meta_synergies_data(company_name: str) -> dict:
    """
    Get Meta synergies data for a company
    
    Args:
        company_name: Name of the company
        
    Returns:
        dict with Meta synergies content
    """
    content = get_meta_synergies.invoke({"company": company_name})
    return {
        "content": content,
        "tab": "meta_synergies"
    }


def get_meta_spend_metrics_data(company_name: str) -> dict:
    """
    Get Meta spend and metrics data for a company
    
    Args:
        company_name: Name of the company
        
    Returns:
        dict with Meta spend and metrics content
    """
    content = get_meta_spend_metrics.invoke({"company": company_name})
    return {
        "content": content,
        "tab": "meta_spend_metrics"
    }


def get_all_highlights(company_name: str) -> dict:
    """
    Get all highlights data for a company
    
    Args:
        company_name: Name of the company
        
    Returns:
        dict with all highlights data
    """
    return {
        "pricing_insights": get_pricing_insights_data(company_name),
        "products_features": get_products_features_data(company_name),
        "ai_cloud_productivity": get_ai_cloud_productivity_data(company_name)
    }
