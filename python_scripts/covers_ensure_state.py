# Sample Service Data
# { "face": "east", "target_state": "morning" }

face = data.get('face', 'all')
if face not in ['all', 'east', 'south', 'west']:
    raise KeyError('Invalid face. Expected all (default), east, south or west, got: {}'.format(face))
target_state = data.get('target_state')
if target_state not in ['morning', 'nighttime', 'sunscreen', 'no-sunscreen']:
    raise KeyError('Invalid target_state. Expected morning, nighttime, sunscreen or no-sunscreen, got: {}'.format(target_state))


def ensure_state(hass, logger, target_state, entity_id):

    current_state = hass.states.get(entity_id)
    if current_state is None:
        logger.error('Error getting current state for entity_id \'{}\' - aborting.'.format(entity_id))
        return
    message_prefix = '*** ENSURE_STATE for cover {} ({}): '.format(current_state.attributes.get('friendly_name'), entity_id)

    if 'ubisys_j1_5502_0000243d' in entity_id or 'ubisys_j1_5502_00000dba' in entity_id:    # Wintergarten Markise, Dachfenster groß
        coverprot_is_active = hass.states.get('input_boolean.coverprot_wind_active').state != 'off'
        if coverprot_is_active:
            logger.info(message_prefix + 'Cover protection is active, aborting.')
            return

    target_lift = None
    target_tilt = None
    ignore_fully_closed = False

    if target_state == 'morning':
        target_lift = 100
    elif target_state == 'nighttime':
        target_lift = 0
        if 'ubisys_j1_5502_0000243d' in entity_id or 'ubisys_j1_5502_00000dba' in entity_id:    # Wintergarten Markise, Dachfenster groß
            target_lift = 100   # Markisen nachts einfahren, nicht ausfahren
    elif target_state == 'sunscreen':
        target_lift = 10
        target_tilt = 50
        ignore_fully_closed = True
        if 'ubisys_j1_5502_00002c8c' in entity_id:  # Küche Terrassentür
            target_lift = 60    # Platz (für die Kinder) zum Durchlaufen
        if 'ubisys_j1_5502_0000243d' in entity_id:  # Wintergarten Markise
            target_lift = 0             # komplett ausfahren
            ignore_fully_closed = False # Markise dient nicht zur Verdunkelung
    elif target_state == 'no-sunscreen':
        target_lift = 100
        ignore_fully_closed = True
        if 'ubisys_j1_5502_0000243d' in entity_id:  # Wintergarten Markise
            ignore_fully_closed = False # Markise dient nicht zur Verdunkelung
    else:
        raise KeyError('Invalid face. Expected morning, nighttime, sunscreen or no-sunscreen, got: {}'.format(target_state))

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


if face in ['east', 'all']:
    ensure_state(hass, logger, target_state, 'cover.ubisys_j1_5502_00002415_1') # Wohnzimmer Sitzfenster
    # ensure_state(hass, logger, target_state, 'cover.ubisys_j1_5502_000024db_1') # Wohnzimmer Terrassentür
    ensure_state(hass, logger, target_state, 'cover.ubisys_j1_5502_00000df3_1') # Florian
    ensure_state(hass, logger, target_state, 'cover.ubisys_j1_5502_00000ded_1') # Jonathan links
    ensure_state(hass, logger, target_state, 'cover.ubisys_j1_5502_00002cc0_1') # Studio DG links
    ensure_state(hass, logger, target_state, 'cover.ubisys_j1_5502_0000240d_1') # Studio DG rechts

if face in ['south', 'all']:
    ensure_state(hass, logger, target_state, 'cover.ubisys_j1_5502_0000243d_1') # Wintergarten Markise
    ensure_state(hass, logger, target_state, 'cover.ubisys_j1_5502_00002c8c_1') # Küche Terrassentür
    ensure_state(hass, logger, target_state, 'cover.ubisys_j1_5502_000024aa_1') # Jonathan rechts
    ensure_state(hass, logger, target_state, 'cover.ubisys_j1_5502_00000dba_1') # Dachfenster groß

if face in ['west', 'all']:
    ensure_state(hass, logger, target_state, 'cover.ubisys_j1_5502_00001110_1') # Windfang
    ensure_state(hass, logger, target_state, 'cover.ubisys_j1_5502_00000dc6_1') # Küche Fenster
    ensure_state(hass, logger, target_state, 'cover.ubisys_j1_5502_0000255e_1') # Schlafzimmer
    ensure_state(hass, logger, target_state, 'cover.ubisys_j1_5502_00000dec_1') # Bad OG
    ensure_state(hass, logger, target_state, 'cover.ubisys_j1_5502_0000243e_1') # Flur OG
    ensure_state(hass, logger, target_state, 'cover.ubisys_j1_5502_00002cec_1') # Bad DG
