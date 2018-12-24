from flask import flash
from wtforms.validators import ValidationError

from app import cache
from app import errors


class Region(object):
    def __call__(self, form, region):
        try:
            if region.data not in sorted(cache.get_regions_from_cache()):
                raise ValidationError('Select region')
        except errors.DatabaseException:
            flash("Internal service's problem", category='alert-danger')
            raise ValidationError('Select region')


class City(object):
    def __call__(self, form, city):
        try:
            regions = cache.get_regions_from_cache()
            region_details = regions.get(form.region.data, None)

            if region_details:
                for city_detail in region_details['cities']:
                    if city_detail['city_name'] == city.data:
                        return

                raise ValidationError('Select city')
        except errors.DatabaseException:
            flash("Internal service's problem", category='alert-danger')
            raise ValidationError('Select city')
