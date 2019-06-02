# Sample Service Data
# { "situation": "morning" }

situation = data.get('situation', 'daytime')
if situation not in ['morning', 'daytime', 'nighttime']:
    raise KeyError('Invalid situation. Expected morning, daytime or nighttime, got: {}'.format(situation))



def ensure_state(hass, logger, situation, sunprot_is_active, entity_id):


    current_state = hass.states.get(entity_id)
    if current_state is None:
        logger.error('Error getting current state for entity_id \'{}\' - aborting.'.format(entity_id))
        return
    message_prefix = '*** ENSURE_STATE for cover {} ({}): '.format(current_state.attributes.get('friendly_name'), entity_id)


    if 'cov_wintergarten_markise' in entity_id or 'cov_dachfenster_gross' in entity_id:
        coverprot_is_active = hass.states.get('input_boolean.coverprot_wind_active').state != 'off'
        if coverprot_is_active:
            logger.info(message_prefix + 'Cover protection is active, aborting.')
            return

    if 'cov_wohnzimmer_terrassentur' in entity_id:
        include_terrassentuer_in_automations = hass.states.get('input_boolean.covers_include_terrassentuer_in_automations').state == 'on'
        if not include_terrassentuer_in_automations:
            logger.debug(message_prefix + 'Cover Terrassentuer is not supposed to be controlled automatically, aborting.')
            return

    if 'cov_kuche_terrassentur' in entity_id:
        include_kuechentuer_in_automations = hass.states.get('input_boolean.covers_include_kuechentuer_in_automations').state == 'on'
        if not include_kuechentuer_in_automations:
            logger.debug(message_prefix + 'Cover Kuechentuer is not supposed to be controlled automatically, aborting.')
            return


    target_lift = None
    target_tilt = None
    ignore_fully_closed = False

    if situation in ['morning', 'daytime']:
        ignore_fully_closed = situation != 'morning'
        if sunprot_is_active:
            target_lift = 10
            target_tilt = 50
            if 'cov_kuche_terrassentur' in entity_id:
                target_lift = 60            # Platz (für die Kinder) zum Durchlaufen
            if 'cov_wintergarten_markise' in entity_id:
                target_lift = 0             # komplett ausfahren
        else:
            target_lift = 100
            if 'cov_wintergarten_markise' in entity_id:
                ignore_fully_closed = False # Markise wird auch zum Sonnenschutz komplett ausgefahren und dient nicht zur Verdunkelung

    elif situation == 'nighttime':
        target_lift = 0
        if 'cov_wintergarten_markise' in entity_id:
            target_lift = 100   # Markisen nachts einfahren, nicht ausfahren

    else:
        raise KeyError('Invalid situation. Expected morning, daytime or nighttime, got: {}'.format(situation))


    current_lift = current_state.attributes.get('current_position')
    current_tilt = current_state.attributes.get('current_tilt_position')

    set_lift = (current_lift is not 'unknown') and (target_lift is not None) and (not ignore_fully_closed or current_lift != 0) and (abs(current_lift - target_lift) > 3)
    set_tilt = (current_tilt is not 'unknown') and (target_tilt is not None) and (not ignore_fully_closed or current_lift != 0) and (abs(current_tilt - target_tilt) > 3)
    
    message = 'target_lift = {}, target_tilt = {}, ignore_fully_closed = {}, current_lift = {}, current_tilt = {}, set_lift = {}, set_tilt = {}'.format(
        target_lift, target_tilt, ignore_fully_closed, current_lift, current_tilt, set_lift, set_tilt)
    if set_lift or set_tilt:
        logger.info(message_prefix + message)
    else:
        logger.debug(message_prefix + message)

    if set_tilt:
        hass.services.call('cover', 'set_cover_tilt_position', {'entity_id': entity_id, 'tilt_position': target_tilt}, False)
        time.sleep(5)

    if set_lift:
        if target_lift == 100 and target_tilt is None:
            hass.services.call('cover', 'open_cover', {'entity_id': entity_id}, False)
        elif target_lift == 0 and target_tilt is None:
            hass.services.call('cover', 'close_cover', {'entity_id': entity_id}, False)
        else:
            hass.services.call('cover', 'set_cover_position', {'entity_id': entity_id, 'position': target_lift}, False)
        time.sleep(5)



sunprot_eastface_is_active = hass.states.get('input_boolean.sunprot_eastface_active').state == 'on'
sunprot_southface_is_active = hass.states.get('input_boolean.sunprot_southface_active').state == 'on'
sunprot_westface_is_active = hass.states.get('input_boolean.sunprot_westface_active').state == 'on'
logger.debug('*** ENSURE_STATE for covers: sunprot_eastface_is_active={}, sunprot_southface_is_active={}, sunprot_westface_is_active={}'.format(sunprot_eastface_is_active, sunprot_southface_is_active, sunprot_westface_is_active))

ensure_state(hass, logger, situation, sunprot_eastface_is_active, 'cover.cov_wohnzimmer_sitzfenster')
ensure_state(hass, logger, situation, sunprot_eastface_is_active, 'cover.cov_wohnzimmer_terrassentur')
ensure_state(hass, logger, situation, sunprot_eastface_is_active or sunprot_southface_is_active or sunprot_westface_is_active, 'cover.cov_wintergarten_markise')
ensure_state(hass, logger, situation, sunprot_southface_is_active, 'cover.cov_kuche_terrassentur')
ensure_state(hass, logger, situation, sunprot_westface_is_active, 'cover.cov_windfang')
ensure_state(hass, logger, situation, sunprot_westface_is_active, 'cover.cov_kuche_fenster')

ensure_state(hass, logger, situation, sunprot_eastface_is_active, 'cover.cov_florian')
ensure_state(hass, logger, situation, sunprot_eastface_is_active, 'cover.cov_jonathan_links')
ensure_state(hass, logger, situation, sunprot_southface_is_active, 'cover.cov_jonathan_rechts')
ensure_state(hass, logger, situation, sunprot_westface_is_active, 'cover.cov_schlafzimmer')
ensure_state(hass, logger, situation, sunprot_westface_is_active, 'cover.cov_bad_og')
ensure_state(hass, logger, situation, sunprot_westface_is_active, 'cover.cov_flur_og')

ensure_state(hass, logger, situation, sunprot_eastface_is_active, 'cover.cov_studio_dg_links')
ensure_state(hass, logger, situation, sunprot_eastface_is_active, 'cover.cov_studio_dg_rechts')
ensure_state(hass, logger, situation, sunprot_southface_is_active or sunprot_westface_is_active, 'cover.cov_dachfenster_gross')
ensure_state(hass, logger, situation, sunprot_westface_is_active, 'cover.cov_bad_dg')
