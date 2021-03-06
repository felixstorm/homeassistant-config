# Sample Service Data
# { "situation": "covers_up" }

situation = data.get('situation', 'default')
valid_situations = ['covers_up', 'covers_up-simulation', 'default', 'evening', 'covers_down', 'covers_down-simulation']
if situation not in valid_situations:
    raise KeyError("Invalid parameter 'situation'. Expected {}, got '{}'".format(valid_situations, situation))
if situation.endswith('-simulation'):
    is_simulation = True
    situation = situation.split('-')[0]
else:
    is_simulation = False

level = data.get('level', None)
if level is not None:
    level = level.split('-')

coverprot_wind_is_active = hass.states.get('input_boolean.coverprot_wind_active').state != 'off'
coverprot_rain_is_active = hass.states.get('input_boolean.coverprot_rain_active').state != 'off'
coverprot_freeze_is_active = hass.states.get('input_boolean.coverprot_freeze_active').state != 'off'
terrassentuer_is_closed = hass.states.get('binary_sensor.f1_senwin_terrassentur_contact').state == 'off'
include_kuechentuer_in_automations = hass.states.get('input_boolean.covers_include_kuechentuer_in_automations').state == 'on'
dachfenster_gross_innen_is_closed = hass.states.get('cover.f3_cov_dachfenster_gross_cover').attributes.get('current_position') == 0
dg_markisen_needed_at_night = hass.states.get('binary_sensor.dg_markisen_needed_at_night').state == 'on'



def ensure_state(entity_id, sunprot_is_active):

    global hass, logger, situation, is_simulation
    global coverprot_wind_is_active, coverprot_rain_is_active, coverprot_freeze_is_active, terrassentuer_is_closed, \
        include_kuechentuer_in_automations, dachfenster_gross_innen_is_closed, dg_markisen_needed_at_night

    current_state = hass.states.get(entity_id)
    if current_state is None:
        logger.error('Error getting current state for entity_id \'{}\' - aborting.'.format(entity_id))
        return
    message_prefix = '*** ENSURE_STATE for {}:'.format(entity_id[6:]).ljust(22 + 37 + 1)


    if terrassentuer_is_closed == False and 'wohnzimmer_terrassentur' in entity_id:
        logger.debug(message_prefix + 'Door Terrassentuer is not closed, aborting.')
        return

    target_lift = None
    target_tilt = None
    skip_if_closed_completely = False

    if situation in ['covers_up', 'default']:
        # tagsüber (manuell) komplett geschlossene Raffstore in Ruhe lassen (Mittagsschlaf, Blendschutz etc.) und
        # Markisen auch morgens (falls sie dann schon manuell komplett ausgefahren worden sind)
        skip_if_closed_completely = (situation != 'covers_up') or ('markise' in entity_id)
        if sunprot_is_active:
            target_lift = 5
            target_tilt = 50
            if 'kuche_terrassentur' in entity_id:
                # Platz (für die Kinder) zum Durchlaufen (und zum Kopf-Anhauen für die Erwachsenen...)
                target_lift = 60
        else:
            target_lift = 100

    elif situation in ['evening', 'covers_down']:
        # Markisen abends & nachts einfahren (außer Dachfenster wg. zusätzlicher Verdunkelung)
        if 'markise' in entity_id:
            target_lift = 100
        # den Rest nachts ausfahren (abends ignorieren)
        elif situation == 'covers_down':
            if is_simulation == False:
                if dg_markisen_needed_at_night == False and ('dachfenster_gross_aussen_cover' in entity_id or 'f3_cov_bad_cover' in entity_id):
                    logger.info(message_prefix + 'Markisen DG are not needed at this time of the year, aborting.')
                    return
                target_lift = 0
            else:
                # bei Simulation nur EG/OG und Markise DG runter und den Rest hochfahren, damit man Licht im DG von
                # außen noch gut sehen kann
                if 'f1' in entity_id or 'f2' in entity_id or 'dachfenster_gross_aussen_cover' in entity_id:
                    target_lift = 0
                else:
                    target_lift = 100

    if target_lift is not None and target_lift != 100:
        if coverprot_wind_is_active and ('markise' in entity_id or 'dachfenster_gross_aussen_cover' in entity_id):
            logger.info(message_prefix + 'Cover protection wind is active, aborting.')
            return
        if coverprot_rain_is_active and 'markise' in entity_id:
            logger.info(message_prefix + 'Cover protection rain is active, aborting.')
            return
        if coverprot_freeze_is_active and ('markise' in entity_id or 'dachfenster_gross_aussen_cover' in entity_id or 'f3_cov_bad_cover' in entity_id):
            logger.info(message_prefix + 'Cover protection freeze is active, aborting.')
            return
        if include_kuechentuer_in_automations == False and 'kuche_terrassentur' in entity_id:
            logger.debug(message_prefix + 'Cover Kuechentuer is not supposed to be controlled automatically, aborting.')
            return

    # None (without quotes) = cover does not support function, 'unknown' (with quotes) = cover does support function,
    # but current state is not known
    current_lift = current_state.attributes.get('current_position')
    current_tilt = current_state.attributes.get('current_tilt_position')

    if situation == 'default' and ('dachfenster_gross_aussen_cover' in entity_id or 'f3_cov_bad_cover' in entity_id) and dachfenster_gross_innen_is_closed and dg_markisen_needed_at_night and current_lift != 0:
        # Wenn die Innenverdunkelung des großen Dachfensters geschlossen ist, dann auch die DG SW-Markisen ausfahren, damit sie z.B. nach
        # Aufhebung von Windalarm nachts automatisch wieder herunter gefahren werden und nicht morgens noch offen sind (und Licht hereinlassen)
        logger.info(message_prefix + 'Also closing this as Dachfenster innen is closed.')
        target_lift = 0

    set_lift = (
        target_lift is not None
        # only set if cover is not closed completely (to allow day-time naps for the kids) or if cover is exempt from it
        # (e.g. in the morning or pure sun shades)
        and (current_lift != 0 or not skip_if_closed_completely)
        # set if current lift state is not known or if cover does not support lift position or if it is known and
        # deviates by more than 3% from target or if cover should close completely but is not tilted completely
        and (current_lift in ['unknown', None] or abs(current_lift - target_lift) > 3 or (target_lift == 0 and current_tilt not in [None, 0]))
    )
    set_tilt = (
        target_tilt is not None
        # only set tilt if supported by cover
        and (current_tilt is not None)
        # only set if cover is not closed completely (to allow day-time naps for the kids) or if cover is exempt from it
        # (e.g. in the morning or pure sun shades)
        and (current_lift != 0 or not skip_if_closed_completely)
        # set if current tilt state is not known or if it is known and deviates by more than 3% from target
        and (current_tilt == 'unknown' or abs(current_tilt - target_tilt) > 3)
    )

    message = ('target_lift = {:>4}, target_tilt = {:>4}, skip_if_closed_completely = {:>4}, current_lift = {:>4}, current_tilt = {:>4}, set_lift = {:>5}, set_tilt = {:>5}'
        .format(str(target_lift), str(target_tilt), str(skip_if_closed_completely), str(current_lift), str(current_tilt), str(set_lift), str(set_tilt)))
    if set_lift or set_tilt:
        logger.info(message_prefix + message)
    else:
        logger.debug(message_prefix + message)

    if set_tilt:
        hass.services.call('cover', 'set_cover_tilt_position', {'entity_id': entity_id, 'tilt_position': target_tilt},
            False)
        time.sleep(5)

    if set_lift:
        # just call open/close if request is to open/close completely without tilt or if cover does not support lift position at all
        if (target_lift == 100 and target_tilt is None) or (current_lift is None and target_lift > 50):
            hass.services.call('cover', 'open_cover', {'entity_id': entity_id}, False)
        elif target_lift == 0 and target_tilt is None or (current_lift is None and target_lift <= 50):
            hass.services.call('cover', 'close_cover', {'entity_id': entity_id}, False)
        else:
            hass.services.call('cover', 'set_cover_position', {'entity_id': entity_id, 'position': target_lift}, False)



sunprot_eastface_is_active = hass.states.get('input_boolean.sunprot_eastface_active').state == 'on'
sunprot_southface_is_active = hass.states.get('input_boolean.sunprot_southface_active').state == 'on'
sunprot_westface_is_active = hass.states.get('input_boolean.sunprot_westface_active').state == 'on'
sunprot_wiga_is_active = hass.states.get('input_boolean.sunprot_wiga_active').state == 'on'
use_terrasse_markise = hass.states.get('input_boolean.covers_use_terrasse_markise_for_sunprotection').state == 'on'

logger.debug('*** ENSURE_STATE for covers: sunprot_eastface_is_active={}, sunprot_southface_is_active={}, sunprot_westface_is_active={}, use_terrasse_markise={}'
    .format(sunprot_eastface_is_active, sunprot_southface_is_active, sunprot_westface_is_active, use_terrasse_markise))
logger.debug('*** ENSURE_STATE for covers: coverprot_wind_is_active={}, coverprot_rain_is_active={}, coverprot_freeze_is_active={}, terrassentuer_is_closed={}'
    .format(coverprot_wind_is_active, coverprot_rain_is_active, coverprot_freeze_is_active, terrassentuer_is_closed))
logger.debug('*** ENSURE_STATE for covers: include_kuechentuer_in_automations={}, dachfenster_gross_innen_is_closed={}, dg_markisen_needed_at_night={}'
    .format(include_kuechentuer_in_automations, dachfenster_gross_innen_is_closed, dg_markisen_needed_at_night))

if level is None or 'eg' in level:
    ensure_state('cover.f1_cov_wohnzimmer_sitzfenster_cover',   sunprot_eastface_is_active)
    # Für den Sonnenschutz werden entweder die Markise oder die Raffstore benötigt, aber nicht beides gleichzeitig.
    ensure_state('cover.f1_cov_wohnzimmer_terrassentur_cover',  sunprot_eastface_is_active and not use_terrasse_markise)
    ensure_state('cover.f1_cov_terrasse_markise_cover',         sunprot_eastface_is_active and use_terrasse_markise)
    ensure_state('cover.f1_cov_wintergarten_markise_cover',     sunprot_wiga_is_active)
    ensure_state('cover.f1_cov_kuche_terrassentur_cover',       sunprot_southface_is_active)
    ensure_state('cover.f1_cov_windfang_cover',                 sunprot_westface_is_active)
    ensure_state('cover.f1_cov_kuche_fenster_cover',            sunprot_westface_is_active)

if level is None or 'og' in level:
    ensure_state('cover.f2_cov_florian_cover',                  sunprot_eastface_is_active)
    ensure_state('cover.f2_cov_jonathan_links_cover',           sunprot_eastface_is_active)
    ensure_state('cover.f2_cov_jonathan_rechts_cover',          sunprot_southface_is_active)
    ensure_state('cover.f2_cov_schlafzimmer_cover',             sunprot_westface_is_active)
    ensure_state('cover.f2_cov_bad_cover',                      sunprot_westface_is_active)
    ensure_state('cover.f2_cov_flur_cover',                     sunprot_westface_is_active)

if level is None or 'dg' in level:
    ensure_state('cover.f3_cov_studio_links_cover',             sunprot_eastface_is_active)
    ensure_state('cover.f3_cov_studio_rechts_cover',            sunprot_eastface_is_active)
    # Die innenliegende Verschattung wird nicht für den Sonnenschutz benutzt, daher ist `sunprot_is_active` immer False.
    ensure_state('cover.f3_cov_dachfenster_gross_cover',        False)
    # Die SW-Dachmarkisen auch bei Südsonne herunterfahren, da es sonst dort sehr warm wird.
    ensure_state('cover.f3_cov_dachfenster_gross_aussen_cover', sunprot_southface_is_active or sunprot_westface_is_active)
    ensure_state('cover.f3_cov_bad_cover',                      sunprot_southface_is_active or sunprot_westface_is_active)
