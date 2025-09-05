class SkillServiceError(Exception):
    """Base exception for skill service errors"""
    def __init__(self, message:str)->None:
        super().__init__(message) 


class SkillExtractionError(SkillServiceError):
    """Raised when skill extraction fails"""
    def __init__(self, message:str)->None:
        super().__init__(message) 


class SkillNormalizationError(SkillServiceError):
    """Raised when skill normalization fails"""
    def __init__(self, message:str)->None:
        super().__init__(message) 


class ModelNotLoadedError(SkillServiceError):
    """Raised when required models are not loaded"""
    def __init__(self, message:str)->None:
        super().__init__(message) 
