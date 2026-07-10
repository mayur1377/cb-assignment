"""Shared helpers for PM scheduling and city routing."""

CITY_ZONAL_OFFICE = {
	"BLR": "Zonal Office - Bengaluru",
	"NCR": "Zonal Office - Delhi/NCR",
	"HYD": "Zonal Office - Hyderabad",
	"CHN": "Zonal Office - Chennai",
	"PUN": "Zonal Office - Pune",
}

FREQUENCY_DAYS = {
	"Weekly": 7,
	"Monthly": 30,
	"Qtrly": 90,
	"Yearly": 365,
	"6 month": 182,
}


def get_zonal_office_for_city(city_code: str) -> str | None:
	return CITY_ZONAL_OFFICE.get((city_code or "").strip().upper())


def add_days_from_frequency(frequency: str, base_date):
	from frappe.utils import add_days, getdate

	days = FREQUENCY_DAYS.get(frequency)
	if not days:
		return None
	return add_days(getdate(base_date), days)
