"""
BEDROT Meta Ads Campaign Name Parser
Created: 2025-08-28
Based on: BEDROT_REFINED_WAREHOUSE_ERD.md campaign parsing logic

Parses Meta Ads campaign names to extract artist, track, and targeting information.
Handles multiple campaign naming patterns from BEDROT's actual Meta Ads data.
"""

import re
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class CampaignParsedData:
    """Structured data extracted from campaign name."""
    artist: Optional[str]
    track: Optional[str] 
    targeting: Optional[str]
    original_name: str


class BEDROTCampaignParser:
    """
    Parser for BEDROT Meta Ads campaign names.
    
    Detected Patterns from Meta Ads Data:
    - "PIG1987 - THE STATE OF THE WORLD - BROAD"
    - "PIG1987 - THE STATE OF THE WORLD - TECHNO"
    - "PIG1987 - THE STATE OF THE WORLD - HARD TRANCE"
    - "PIG1987 - THE STATE OF THE WORLD - BROAD SPOTIFY"
    - "THE SOURCE - Streaming" (ZONE A0 implied)
    - "IWARY - BROAD"
    - "IWARY - BROAD MALE"
    - "IWARY - TECHNO SPOTIFY - Copy"
    - "New Engagement Ad Set" (generic campaign)
    """
    
    # Known artists for validation
    KNOWN_ARTISTS = {
        'PIG1987', 'ZONE A0', 'XXMEATWARRIOR69XX', 'IWARY', 'ZONE A0 X SXNCTUARY'
    }
    
    # Known tracks for validation (from campaign analysis)
    KNOWN_TRACKS = {
        'THE STATE OF THE WORLD', 'THE SOURCE', 'RENEGADE PIPELINE', 
        'THE SCALE', 'IWARY', 'TRANSFORMER ARCHITECTURE'
    }
    
    def parse_campaign_name(self, campaign_name: str) -> CampaignParsedData:
        """
        Extract artist, track, and targeting from Meta campaign names.
        
        Args:
            campaign_name: Raw campaign name from Meta Ads
            
        Returns:
            CampaignParsedData with parsed components
        """
        original_name = campaign_name.strip()
        campaign_upper = original_name.upper()
        
        # Handle generic engagement campaigns
        if "NEW ENGAGEMENT" in campaign_upper:
            return CampaignParsedData(
                artist=None,
                track=None,
                targeting="ENGAGEMENT",
                original_name=original_name
            )
        
        # Clean campaign name (remove " - Copy" suffixes)
        cleaned_name = re.sub(r'\s*-\s*Copy\s*$', '', campaign_upper, flags=re.IGNORECASE)
        
        # Split by " - " delimiter
        parts = [part.strip() for part in cleaned_name.split(' - ')]
        
        if len(parts) == 1:
            # Single part - treat as targeting
            return CampaignParsedData(
                artist=None,
                track=None,
                targeting=parts[0],
                original_name=original_name
            )
        
        elif len(parts) == 2:
            # Two parts - could be "TRACK - TARGETING" or "ARTIST - TRACK"
            part1, part2 = parts
            
            # Check if first part is a known track without artist prefix
            if part1 in self.KNOWN_TRACKS:
                # Format: "THE SOURCE - Streaming" (ZONE A0 implied)
                return CampaignParsedData(
                    artist="ZONE A0",  # Default for non-prefixed tracks
                    track=part1,
                    targeting=part2,
                    original_name=original_name
                )
            
            # Check if first part is a known artist
            elif part1 in self.KNOWN_ARTISTS:
                # Format: "IWARY - BROAD" (track name same as artist)
                return CampaignParsedData(
                    artist=part1,
                    track=part1,  # Track name matches artist for single-name releases
                    targeting=part2,
                    original_name=original_name
                )
            
            else:
                # Default: treat as track - targeting
                return CampaignParsedData(
                    artist=None,
                    track=part1,
                    targeting=part2,
                    original_name=original_name
                )
        
        elif len(parts) >= 3:
            # Three or more parts: "ARTIST - TRACK - TARGETING"
            artist = parts[0]
            track = parts[1]
            targeting = " - ".join(parts[2:])  # Join remaining parts as targeting
            
            return CampaignParsedData(
                artist=artist,
                track=track,
                targeting=targeting,
                original_name=original_name
            )
        
        else:
            # Fallback for empty or malformed names
            return CampaignParsedData(
                artist=None,
                track=None,
                targeting=campaign_upper if campaign_upper else "UNKNOWN",
                original_name=original_name
            )
    
    def validate_parsed_data(self, parsed: CampaignParsedData) -> Dict[str, bool]:
        """
        Validate parsed campaign data against known artists/tracks.
        
        Returns:
            Dict with validation results for artist, track, and overall validity
        """
        return {
            'artist_valid': parsed.artist is None or parsed.artist in self.KNOWN_ARTISTS,
            'track_valid': parsed.track is None or parsed.track in self.KNOWN_TRACKS,
            'has_targeting': parsed.targeting is not None and len(parsed.targeting.strip()) > 0,
            'is_valid': True  # Basic validation - campaign name was parseable
        }


def parse_campaign_batch(campaign_names: list) -> Dict[str, CampaignParsedData]:
    """
    Parse multiple campaign names at once.
    
    Args:
        campaign_names: List of campaign name strings
        
    Returns:
        Dict mapping original campaign names to parsed data
    """
    parser = BEDROTCampaignParser()
    results = {}
    
    for name in campaign_names:
        results[name] = parser.parse_campaign_name(name)
    
    return results


# Example usage and testing
if __name__ == "__main__":
    # Test with actual campaign names from Meta Ads data
    test_campaigns = [
        "PIG1987 - THE STATE OF THE WORLD - BROAD",
        "IWARY - BROAD",
        "IWARY - BROAD MALE", 
        "IWARY - BROAD SPOTIFY",
        "IWARY - TECHNO SPOTIFY - Copy",
        "PIG1987 - THE STATE OF THE WORLD - BROAD SPOTIFY",
        "PIG1987 - THE STATE OF THE WORLD - HARD TRANCE",
        "PIG1987 - THE STATE OF THE WORLD - TECHNO",
        "THE SOURCE - Streaming",
        "New Engagement Ad Set",
        "THE SCALE",
        "RENEGADE PIPELINE"
    ]
    
    parser = BEDROTCampaignParser()
    
    print("BEDROT Campaign Parser Test Results")
    print("=" * 50)
    
    for campaign in test_campaigns:
        parsed = parser.parse_campaign_name(campaign)
        validation = parser.validate_parsed_data(parsed)
        
        print(f"\nCampaign: {campaign}")
        print(f"  Artist: {parsed.artist}")
        print(f"  Track: {parsed.track}")
        print(f"  Targeting: {parsed.targeting}")
        print(f"  Valid: {validation}")