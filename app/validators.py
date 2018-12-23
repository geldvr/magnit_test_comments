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

# class Region(object):
#     def __init__(self):
#         self.message = u'Регион {REGION} не найден'
#         self.db_instance = db.PostgresDB()
#
#     def __call__(self, form, region):
#         query_stmt = """
#             SELECT region_name
#                 FROM regions
#                 WHERE region_name = '{REGION}'
#         """
#
#         try:
#             if not self.db_instance.query(query_stmt.format(REGION=region.data)):
#                 logging.debug("invalid region[%s] received", region.data)
#                 raise ValidationError(self.message.format(REGION=region.data))
#         except errors.DatabaseException as db_err:
#             raise ValidationError(str(db_err))


# class City(object):
#     def __init__(self):
#         self.message = u'Not found in region'
#         self.db_instance = db.PostgresDB()
#
#     def __call__(self, form, city):
#         query_stmt = """
#             SELECT region_name, city_name, city_id
#                 FROM regions r JOIN cities c ON r.region_id = c.region_id
#                 WHERE region_name = '{REGION}' AND city_name = '{CITY}';
#         """
#
#         try:
#             query_results = self.db_instance.query(query_stmt.format(REGION=form.region.data, CITY=city.data))
#             if not query_results:
#                 logging.debug("received form data with invalid region-city pair[%s/%s]", form.region.data, city.data)
#                 raise ValidationError(self.message)
#
#             # Assign city id
#             city.data = query_results[0][-1]
#         except errors.DatabaseException as db_err:
#             raise ValidationError(str(db_err))


# class City(object):
#     def __call__(self, form, city):
#         try:
#             regions_cities = cache.get_regions_cities_from_cache()
#             cached_cities_for_region = regions_cities.get(form.region.data, None)
#             if cached_cities_for_region and city.data not in cached_cities_for_region:
#                 raise ValidationError('Select city')
#         except errors.DatabaseException:
#             flash("Internal service's problem", category='alert-danger')
#             raise ValidationError('Select city')
