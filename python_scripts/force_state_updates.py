group_name = "group.{}".format(data.get('group_name', 'invalid_group'))
group = hass.states.get(group_name)
if group is None:
    raise KeyError("Unable to find group '{}'.".format(group_name))

entity_ids = []
for entity_id in group.attributes["entity_id"]:
    logger.debug("Forcefully updating state of entity '{}'.".format(entity_id))
    current_state = hass.states.get(entity_id)
    hass.states.set(entity_id, current_state.state , current_state.attributes, force_update=True)
    entity_ids.append(entity_id)

logger.info("Forcefully updated states of entities {}.".format(entity_ids))
