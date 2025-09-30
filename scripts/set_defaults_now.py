from src import database

if __name__ == '__main__':
    print('Setting 99024 and 99214 as default billing codes...')
    ok = database.set_default_billing_codes(['99024','99214'])
    print('set_default_billing_codes returned:', ok)

    print('\nVerifying task_billing_codes rows for Primary Care Visit:')
    rows = database.get_billing_codes(service_type='Primary Care Visit')
    if not rows:
        print('No rows returned for Primary Care Visit')
    else:
        for r in rows:
            print(r.get('billing_code'), '| is_default=', r.get('is_default'), '| description=', r.get('description'))
