from enum import Enum


class SceneType(str, Enum):

    NORMAL = "normal"

    START = "start"

    END = "end"

    MENU = "menu"

    FORM = "form"

    QUESTION = "question"

    AI = "ai"

    FILE = "file"

    PAYMENT = "payment"

    CRM = "crm"

    API = "api"

    WEBHOOK = "webhook"


class ScenePurpose(str, Enum):

    GREETING = "greeting"

    INFORMATION = "information"

    EDUCATION = "education"

    PRESENTATION = "presentation"

    SALES = "sales"

    LEAD = "lead"

    CONTACT = "contact"

    SUPPORT = "support"

    CONSULTATION = "consultation"

    PAYMENT = "payment"

    ORDER = "order"

    REGISTRATION = "registration"

    SURVEY = "survey"

    FEEDBACK = "feedback"

    THANKS = "thanks"

    FINISH = "finish"


class Emotion(str, Enum):

    NEUTRAL = "neutral"

    INTEREST = "interest"

    CURIOSITY = "curiosity"

    CONFUSION = "confusion"

    DOUBT = "doubt"

    TRUST = "trust"

    PURCHASE = "purchase"

    DELIGHT = "delight"

    FRUSTRATION = "frustration"

    ANGER = "anger"


class DecisionType(str, Enum):

    BUTTON = "button"

    AUTO = "auto"

    CONDITION = "condition"

    AI = "ai"

    TIMEOUT = "timeout"

    WEBHOOK = "webhook"


class AttachmentType(str, Enum):

    IMAGE = "image"

    VIDEO = "video"

    AUDIO = "audio"

    DOCUMENT = "document"

    PDF = "pdf"

    DOCX = "docx"

    XLSX = "xlsx"

    ZIP = "zip"

    URL = "url"

    HTML = "html"


class ActionType(str, Enum):

    SAVE_VARIABLE = "save_variable"

    SAVE_FORM = "save_form"

    SEND_EMAIL = "send_email"

    SEND_TELEGRAM = "send_telegram"

    CREATE_LEAD = "create_lead"

    CREATE_ORDER = "create_order"

    CREATE_TICKET = "create_ticket"

    HTTP_REQUEST = "http_request"

    WEBHOOK = "webhook"

    OPEN_AI = "open_ai"

    GENERATE_FILE = "generate_file"

    DOWNLOAD = "download"

    PAYMENT = "payment"

    SQL = "sql"

    PYTHON = "python"

    CUSTOM = "custom"


class FieldType(str, Enum):

    TEXT = "text"

    PHONE = "phone"

    EMAIL = "email"

    NUMBER = "number"

    DATE = "date"

    TIME = "time"

    CHECKBOX = "checkbox"

    RADIO = "radio"

    SELECT = "select"

    TEXTAREA = "textarea"

    FILE = "file"

    LOCATION = "location"


class AnalyticsLevel(str, Enum):

    NONE = "none"

    BASIC = "basic"

    ADVANCED = "advanced"

    FULL = "full"