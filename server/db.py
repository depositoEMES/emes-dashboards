import os
import json
import logging
import firebase_admin
from firebase_admin import db
from typing import Callable, Any, Dict, List


logging.basicConfig(
    filename="db.log",
    format='%(asctime)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    level=logging.INFO
)


class Database:

    COLLECTIONS = \
        [
            "convenios",
            "cartera_actual",
            "ventas_vendedor",
            "recibos_caja",
            "num_clientes_por_vendedor"
        ]

    def __init__(self):
        """
        Constructor.

        Args:
            user_data (Dict[str, Dict[str, Any]]): User permission.

        Raises:
            Exception: unauthorized firebase admin session
        """
        credentials = os.environ.get('FIREBASE_CREDENTIALS')
        db_url = os.environ.get('FIREBASE_URL')

        cred_dict = json.loads(credentials)

        self.cred_firebase = \
            firebase_admin.credentials.Certificate(cert=cred_dict)

        if not firebase_admin._apps:
            self.__app = firebase_admin.initialize_app(
                self.cred_firebase,
                {
                    'databaseURL': db_url
                }
            )

            if self.__app:
                self.ref = \
                    {
                        collection: db.reference(f"/{collection}/")
                        for collection in Database.COLLECTIONS
                    }

                self.listener = \
                    {
                        collection: None
                        for collection in Database.COLLECTIONS
                    }
            else:
                raise Exception("Error creating Firebase object")

    @property
    def collections(self) -> List[str]:
        return Database.COLLECTIONS

    def push(
            self,
            collection: str,
            data: Dict[str, Any]) -> bool:
        """
        Insert new data into database collection

        Args:
            collection (str): Collection name
            data (Dict[str, Any]): Collection formatted data

        Returns:
            bool: True if response was succesfull
        """
        try:
            if collection in Database.COLLECTIONS:
                self.ref[collection].push().set(data)

            return True

        except Exception as e:
            logging.error(
                f"Error al insertar un nuevo dato en la colección {
                    collection} >> > {e}",
                exc_info=True
            )
            return False

    def where(
            self,
            collection: str,
            item: str,
            value: Any) -> Dict[str, Any] | None:
        """
        Returns the query where items are equal to given value.

        Args:
            collection (str): Collection name.
            key (str): Item name (eg. "estado").
            value (Any): Value (eg. -1).

        Returns:
            Dict[str, Any] | None: Specified value
        """
        try:
            if collection in Database.COLLECTIONS:
                # Get query based on specified collection
                query = self.ref[collection].order_by_child(
                    item).equal_to(value).get()

                if len(query) > 0:
                    out_values = \
                        {
                            key: value
                            for key, value in query.items()
                        }

                    return out_values

        except Exception as e:
            logging.error(
                f"Error al hacer la query(where) en la colección {collection} {
                    collection} >> > {e}",
                exc_info=True
            )

    def where_range(
            self,
            collection: str,
            key: str,
            start_value: Any,
            end_value: Any | None) -> Dict[str, Any] | None:
        """
        Returns the query where items are different to given value.

        Args:
            collection (str): Collection name.
            key (str): Item name (eg. "estado").
            start_value (Any): From value (eg. 0).
            end_value (Any | None): To value (eg. 2). None if no range.

        Returns:
            Dict[str, Any] | None: Specified value
        """
        try:
            if collection in Database.COLLECTIONS:
                # Get query based on specified collection
                query = self.ref[collection].order_by_child(
                    key).start_at(start_value).end_at(end_value).get()

                if len(query) > 0:
                    out_values = \
                        {
                            key: value
                            for key, value in query.items()
                        }

                    return out_values

        except Exception as e:
            logging.error(
                f"Error al hacer la query(where_range) en la colección {collection} {
                    collection} >> > {e}",
                exc_info=True
            )

    def exists(
            self,
            collection: str,
            item: str,
            value: Any) -> bool:
        """
        Checks if there is an item with the specified value

        Args:
            collection (str): Collection name
            item (str): Item name (eg. factura)
            value (Any): Value (eg. 548492)

        Returns:
            bool: True if item code exists
        """
        try:
            query = self.where(collection, item, value)
            values = list(query.values())[0] if query else None

            return False if not values else values["estado"] != -1

        except Exception as e:
            logging.error(
                f"Error al revisar si existe un item con el valor especificado en la base de datos >> > {
                    e}",
                exc_info=True
            )
            return False

    def update_by_key(
            self,
            collection: str,
            key: Any,
            value: dict) -> bool:
        """
        Update DB state value

        Args:
            collection (str): Collection name
            key (Any): Document key
            value (dict): Data to modify 
        """
        try:
            if collection in Database.COLLECTIONS:
                self.ref[collection].child(key).update(value)

            return True

        except Exception as e:
            logging.error(
                f"Error al actualizar la colección {
                    collection} de la base de datos con el key {key} >> > {e}",
                exc_info=True
            )
            return False

    def update_by_path(self, path: str, value: Any) -> bool:
        """
        Update specified reference data with given data.

        Args:
            path (str): Reference path.
            value (Any): Reference value.

        Returns:
            bool: True if reference was successfully updated.
        """
        try:
            ref = db.reference(path)
            ref.update(value)

            return True

        except Exception as e:
            logging.error(
                f"Error al actualizar la ruta {
                    path} de la base de datos >> > {e}",
                exc_info=True
            )
            return False

    def update(self, collection: str, value: Any) -> bool:
        """
        Add all collection data in one API call 

        Args:
            collection (str): Collection name
            value (Any): JSON-like value

        Returns:
            bool: True if reference was successfully updated
        """
        try:
            if collection in Database.COLLECTIONS:
                self.ref[collection].update(value)

            return True

        except Exception as e:
            logging.error(
                f"Error al actualizar la colección {
                    collection} de la base de datos >> > {e}",
                exc_info=True
            )
            return False

    def insert(
            self,
            collection: str,
            data: Dict[str, Any]) -> bool:
        """
        Insert data in specified collection one by one.

        Args:
            collection (str): Collection name.
            data (Dict[str, Any]): Data to save in database.

        Returns:
            bool: True if data was inserted into specified collection. 
        """
        response = False

        try:
            if collection in Database.COLLECTIONS:
                # Iterate over the dictionary
                for key, value in data.items():
                    # Check if the key already exists in the database
                    if not self.ref[collection].child(key).get():
                        self.ref[collection].child(key).set(value)

                response = True

        except Exception as e:
            logging.error(
                f"Error al insertar datos en la colección {
                    collection} >> > {e}",
                exc_info=True
            )

        return response

    def get_by_path(self, path: str) -> Any | None:
        """
        Get specified reference data

        Args:
            path (str): Reference path

        Returns:
            Any: Reference path data
        """
        try:
            ref = db.reference(path)

            return ref.get() if ref else None

        except Exception as e:
            logging.error(
                f"Error al obtener datos de la ruta {path} >>> {e}",
                exc_info=True
            )

    def get_by_key(
            self,
            collection: str,
            key: str) -> Dict[str, Any] | None:
        """
        Get data from specified key child in given collection

        Args:
            collection (str): Collection name
            key (str): Document key

        Returns:
            Dict[str, Any] | None: Document data
        """
        try:
            return self.ref[collection].child(key).get()

        except Exception as e:
            logging.error(
                f"Error al obtener datos de la colección {
                    collection} con key: {key} >> > {e}",
                exc_info=True
            )

    def get(self, collection: str) -> Dict[str, Any] | None:
        """
        Returns the information of specified collection

        Returns:
            collection (str): Collection name
        """
        try:
            if collection in Database.COLLECTIONS:
                # Get results from given collection
                results = self.ref[collection].get()

                if results:
                    return \
                        {
                            key: value
                            for key, value in results.items()
                        }

        except Exception as e:
            logging.error(
                f"Error al obtener datos de la colección {collection} >>> {e}",
                exc_info=True
            )

    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Get database data.

        Returns:
            Dict[str, Dict[str, Any]]: Database data.
        """
        try:
            ref = db.reference()

            if ref:
                return ref.get()

        except Exception as e:
            logging.error(
                f"Error al obtener los datos de todas las colecciones de la base de datos >> > {
                    e}",
                exc_info=True
            )

    def delete_by_key(self, collection: str, key: str) -> bool:
        """
        Delete data from specified collection based con key.

        Args:
            collection (str): Collection name.
            key (str): Collection child key.

        Returns:
            bool: True if reference was successfully updated.
        """
        try:
            if collection in Database.COLLECTIONS:
                self.ref[collection].child(key).delete()

            return True

        except Exception as e:
            logging.error(
                f"Error al borrar el valor {
                    key} datos de la colección {collection} >> > {e}",
                exc_info=True
            )
            return False

    def delete(self, collection: str) -> bool:
        """
        Delete data from specified collection based con key.

        Args:
            collection (str): Collection name.

        Returns:
            bool: True if reference was successfully updated.
        """
        try:
            if collection in Database.COLLECTIONS:
                self.ref[collection].delete()

            return True

        except Exception as e:
            logging.error(
                f"Error al borrar la colección {collection} >>> {e}",
                exc_info=True
            )
            return False

    def start_listener(
            self,
            collection: str,
            callback: Callable) -> None:
        """
        Start the specified listener to listen for real-time events from Firebase.

        Args:
            collection (str): Collection name
            callback (Callable): Callback function
        """
        try:
            if collection in Database.COLLECTIONS:
                self.listener[collection] = \
                    self.ref[collection].listen(callback)

        except Exception as e:
            logging.error(
                f"Error al inicializar el listener de la colección {
                    collection} >> > {e}",
                exc_info=True
            )

    def start_listeners(self, callback: Callable) -> None:
        """
        Starts the listener to listen for real-time events from Firebase.

        Args:
            callback (Callable): Function to be executed when events are received.
        """
        try:
            for collection in Database.COLLECTIONS:
                if callback[collection] is not None:
                    self.listener[collection] = \
                        self.ref[collection].listen(callback[collection])

        except Exception as e:
            logging.error(
                f"Error al inicializar los listeners especificados >>> {e}",
                exc_info=True
            )

    def __stop_listeners(self) -> None:
        """
        Stops the all the collections listener
        """
        try:
            for collection in Database.COLLECTIONS:
                if self.listener[collection]:
                    self.listener[collection].close()

        except Exception as e:
            logging.error(
                f"Error al detener los listeners creados >>> {e}",
                exc_info=True
            )

    def stop_connection(self) -> None:
        """
        Stops the connection to Firebase and deletes the app
        """
        try:
            # Stop the listener first to ensure the connection is closed properly
            self.__stop_listeners()

            # Delete the Firebase app to clean up resources and terminate the connection
            firebase_admin.delete_app(self.__app)

        except Exception as e:
            logging.error(
                f"Error al detener la conexión con la base de datos >>> {e}",
                exc_info=True
            )
