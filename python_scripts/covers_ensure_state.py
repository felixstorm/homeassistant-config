# Sample Service Data
# { "situation": "morning" }

situation = data.get('situation', 'daytime')
if situation not in ['morning', 'daytime', 'evening', 'nighttime']:
    raise KeyError('Invalid situation. Expected morning, daytime, evening or nighttime, got: {}'.format(situation))



def ensure_state(hass, logger, situation, sunprot_is_active, entity_id):


    current_state = hass.states.get(entity_id)
    if current_state is None:
        logger.error('Error getting current state for entity_id \'{}\' - aborting.'.format(entity_id))
        return
    message_prefix = '*** ENSURE_STATE for {}:'.format(entity_id).ljust(61)


    if 'markise' in entity_id or 'dachfenster_gross' in entity_id:
        coverprot_is_active = hass.states.get('binary_sensor.coverprot_active').state != 'off'
        if coverprot_is_active:
            logger.info(message_prefix + 'Cover protection is active, aborting.')
            return

    if 'wohnzimmer_terrassentur' in entity_id:
        include_terrassentuer_in_automations = hass.states.get('input_boolean.covers_include_terrassentuer_in_automations').state == 'on'
        if not include_terrassentuer_in_automations:
            logger.debug(message_prefix + 'Cover Terrassentuer is not supposed to be controlled automatically, aborting.')
            return

    if 'terrasse_markise' in entity_id:
        include_terrasse_markise_in_automations = hass.states.get('input_boolean.covers_include_terrasse_markise_in_automations').state == 'on'
        if not include_terrasse_markise_in_automations:
            logger.debug(message_prefix + 'Cover Terrasse Markise is not supposed to be controlled automatically, aborting.')
            return

    if 'kuche_terrassentur' in entity_id:
        include_kuechentuer_in_automations = hass.states.get('input_boolean.covers_include_kuechentuer_in_automations').state == 'on'
        if not include_kuechentuer_in_automations:
            logger.debug(message_prefix + 'Cover Kuechentuer is not supposed to be controlled automatically, aborting.')
            return


    target_lift = None
    target_tilt = None
    skip_if_closed_completely = False

    if situation in ['morning', 'daytime']:
        skip_if_closed_completely = situation != 'morning'
        if sunprot_is_active:
            target_lift = 5
            target_tilt = 50
            if 'kuche_terrassentur' in entity_id:
                target_lift = 60    # Platz (für die Kinder) zum Durchlaufen (und zum Kopf-Anhauen für die Erwachsenen...)
        else:
            target_lift = 100

    elif situation in ['evening', 'nighttime']:
        if 'markise' in entity_id:
            target_lift = 100       # Markisen abends/nachts einfahren
        elif situation == 'nighttime':
            target_lift = 0         # den Rest nachts ausfahren (abends ignorieren)

    # None (without quotes) = cover does not support function, 'unknown' (with quotes) = cover does support function, but current state is not known
    current_lift = current_state.attributes.get('current_position')
    current_tilt = current_state.attributes.get('current_tilt_position')

    set_lift = (
        target_lift is not None
        # only set if cover is not closed completely (to allow day-time naps for the kids) or if cover is exempt from it (e.g. in the morning or pure sun shades)
        and (current_lift != 0 or not skip_if_closed_completely)
        # set if current lift state is not known or if cover does not support lift position or if it is known and deviates by more than 3% from target
        and (current_lift in ['unknown', None] or abs(current_lift - target_lift) > 3)
    )
    set_tilt = (
        target_tilt is not None
        # only set tilt if supported by cover
        and (current_tilt is not None)
        # only set if cover is not closed completely (to allow day-time naps for the kids) or if cover is exempt from it (e.g. in the morning or pure sun shades)
        and (current_lift != 0 or not skip_if_closed_completely)
        # set if current tilt state is not known or if it is known and deviates by more than 3% from target
        and (current_tilt is 'unknown' or abs(current_tilt - target_tilt) > 3)
    )

    message = 'target_lift = {:>4}, target_tilt = {:>4}, skip_if_closed_completely = {:>4}, current_lift = {:>4}, current_tilt = {:>4}, set_lift = {:>5}, set_tilt = {:>5}'.format(
        str(target_lift), str(target_tilt), str(skip_if_closed_completely), str(current_lift), str(current_tilt), str(set_lift), str(set_tilt))
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
sunprot_wiga_is_active = hass.states.get('input_boolean.sunprot_wiga_active').state == 'on'
logger.debug('*** ENSURE_STATE for covers: sunprot_eastface_is_active={}, sunprot_southface_is_active={}, sunprot_westface_is_active={}'.format(sunprot_eastface_is_active, sunprot_southface_is_active, sunprot_westface_is_active))

ensure_state(hass, logger, situation, sunprot_eastface_is_active, 'cover.cov_wohnzimmer_sitzfenster_cover')
ensure_state(hass, logger, situation, sunprot_eastface_is_active, 'cover.cov_wohnzimmer_terrassentur_cover')
ensure_state(hass, logger, situation, sunprot_eastface_is_active, 'cover.cov_terrasse_markise_cover')
ensure_state(hass, logger, situation, sunprot_wiga_is_active, 'cover.cov_wintergarten_markise_cover')
ensure_state(hass, logger, situation, sunprot_southface_is_active, 'cover.cov_kuche_terrassentur_cover')
ensure_state(hass, logger, situation, sunprot_westface_is_active, 'cover.cov_windfang_cover')
ensure_state(hass, logger, situation, sunprot_westface_is_active, 'cover.cov_kuche_fenster_cover')

ensure_state(hass, logger, situation, sunprot_eastface_is_active, 'cover.cov_florian_cover')
ensure_state(hass, logger, situation, sunprot_eastface_is_active, 'cover.cov_jonathan_links_cover')
ensure_state(hass, logger, situation, sunprot_southface_is_active, 'cover.cov_jonathan_rechts_cover')
ensure_state(hass, logger, situation, sunprot_westface_is_active, 'cover.cov_schlafzimmer_cover')
ensure_state(hass, logger, situation, sunprot_westface_is_active, 'cover.cov_bad_og_cover')
ensure_state(hass, logger, situation, sunprot_westface_is_active, 'cover.cov_flur_og_cover')

ensure_state(hass, logger, situation, sunprot_eastface_is_active, 'cover.cov_studio_dg_links_cover')
ensure_state(hass, logger, situation, sunprot_eastface_is_active, 'cover.cov_studio_dg_rechts_cover')
ensure_state(hass, logger, situation, sunprot_southface_is_active or sunprot_westface_is_active, 'cover.cov_dachfenster_gross_cover')
# ensure_state(hass, logger, situation, sunprot_westface_is_active, 'cover.cov_bad_dg_cover')  # Do not control Bad DG automatically for now (to be able to keep it always down)
