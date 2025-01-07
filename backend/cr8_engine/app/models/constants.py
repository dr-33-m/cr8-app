

class UserRole:
    CONTENT_CREATOR = "content_creator"
    CG_ARTIST = "cg_artist"


class SubscriptionTier:
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"


class AssetType:
    CLOTHING = "clothing"
    SHOES = "shoes"
    FURNITURE = "furniture"
    JEWELRY = "jewelry"
    VEHICLE = "vehicle"
    OTHER = "other"


class ProjectStatus:
    DRAFT = "draft"
    FINISHED = "finished"


class ProjectType:
    MUSIC = "music"
    PRODUCT = "product"
    FASHION = "fashion"
    SOCIAL_MEDIA = "socialMedia"


class MusicSubtype:
    ART_COVER = "Art Cover"
    VISUALIZER = "Visualizer"
    MUSIC_VIDEO = "Music Video"


class ProductSubtype:
    PRODUCT_SHOOT = "Product Shoot"
    PRODUCT_REEL = "Product Reel"
    PRODUCT_CAMPAIGN = "Product Campaign"


class FashionSubtype:
    LOOK_SHOOT = "Look Shoot"
    LOOK_REEL = "Look Reel"
    FASHION_SHOW = "Fashion Show"


class SocialMediaSubtype:
    POST = "Post"
    REEL = "Reel"
    CAMPAIGN = "Campaign"


class Theme:
    minimalist = "minimalist"
    futuristic = "futuristic"
    rustic = "rustic"
    industrial = "industrial"
    vibrant = "vibrant"
    custom = "custom"


class Tone:
    joyful = "joyful"
    melancholic = "melancholic"
    energetic = "energetic"
    serene = "serene"
    bold = "bold"
    dreamy = "dreamy"


class Industry:
    fashion = "fashion"
    music = "music"
    real_estate = "real-estate"
    tech = "tech"
    entertainment = "entertainment"
    custom = "custom"


class UsageIntent:
    product_launch = "product-launch"
    music_video = "music-video"
    social_media = "social-media"
    commercial = "commercial"
