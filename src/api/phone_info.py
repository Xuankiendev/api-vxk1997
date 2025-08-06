from sqlalchemy.orm import Session
from ..auth import validateApiKey
import phonenumbers
from phonenumbers import geocoder, carrier, number_type
from phonenumbers.phonenumberutil import number_type as nt

async def run(params: dict, db: Session):
    await validateApiKey(params["apiKey"], db)

    phone_number = params.get("phonenumber")
    if not phone_number:
        return {"error": "Missing phonenumber parameter"}

    try:
        parsed = phonenumbers.parse(phone_number)

        info = {
            "number": phone_number,
            "valid": phonenumbers.is_valid_number(parsed),
            "region": geocoder.description_for_number(parsed, "en"),
            "country_code": parsed.country_code,
            "formatted": f"+{parsed.country_code}{parsed.national_number}",
            "location": geocoder.description_for_number(parsed, "vi"),
            "carrier": carrier.name_for_number(parsed, "vi"),
            "type": {
                nt.MOBILE: "Mobile",
                nt.FIXED_LINE: "Fixed line",
                nt.FIXED_LINE_OR_MOBILE: "Fixed or Mobile",
                nt.TOLL_FREE: "Toll Free",
                nt.VOIP: "VoIP",
                nt.PERSONAL_NUMBER: "Personal",
                nt.PAGER: "Pager",
                nt.UAN: "UAN",
                nt.UNKNOWN: "Unknown"
            }.get(number_type(parsed), "Unknown")
        }

        return info

    except Exception as e:
        return {"error": str(e)}
