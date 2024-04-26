### Established Database Connection
```shell
 curl -X POST -H "Content-Type: application/json" -d '{"db_config": {"db_type": "mysql", "host": "localhost", "port": "3305", "username": "root", "password": "root", "database_schema": "nasa_space_exploration_database"}}' http://127.0.0.1:5000/set_db_config
```

### Post User Prompt to get the SQL Response
```shell
curl -X POST -H "Content-Type: application/json" -d '{"user_prompt": "Get All the Astronaut"}' http://127.0.0.1:5000/user_prompt
```