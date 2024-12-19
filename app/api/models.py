from typing import Optional, List, Dict

from pydantic import BaseModel


# 请求模型
class InitialIdeaRequest(BaseModel):
    """初始创意输入"""
    idea_description: str
    target_audience: Optional[str] = None
    style_preference: Optional[str] = None
    token_name: Optional[str] = None


class DesignSelectionRequest(BaseModel):
    """设计方案选择"""
    session_id: str
    selected_design_id: str


class MarketingPlanRequest(BaseModel):
    """营销计划确认"""
    session_id: str
    selected_plan_id: str
    customizations: Optional[Dict] = None


# 响应模型
class CreativeProposalResponse(BaseModel):
    """创意提案响应"""
    session_id: str
    proposals: List[Dict]
    market_analysis: Dict
    next_steps: List[str]


class DesignOptionsResponse(BaseModel):
    """设计方案响应"""
    session_id: str
    designs: List[Dict]
    analysis: Dict
    recommendations: List[str]


class FinalPackageResponse(BaseModel):
    """最终交付包响应"""
    token_details: Dict
    design_assets: Dict
    marketing_materials: Dict
    deployment_guide: Dict