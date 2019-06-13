import dbus


class systemd(object):

    UNIT_INTERFACE = "org.freedesktop.systemd1.Unit"
    SERVICE_UNIT_INTERFACE = "org.freedesktop.systemd1.Service"

    def __init__(self):
        self.__bus = dbus.SystemBus()

    def disable(self, name):
        interface = self._get_interface()

        if interface is None:
            return False

        try:
            interface.DisableUnitFiles([name], dbus.Boolean(False))
            return True
        except dbus.exceptions.DBusException as error:
            print(error)
            return False

    def enable(self, name):
        interface = self._get_interface()

        if interface is None:
            return False

        try:
            interface.EnableUnitFiles([name],
                                      dbus.Boolean(False),
                                      dbus.Boolean(True))
            return True
        except dbus.exceptions.DBusException as error:
            print(error)
            return False

    def get_active_state(self, name):
        properties = self._get_unit_properties(name, self.UNIT_INTERFACE)

        if properties is None:
            return False

        try:
            state = properties["ActiveState"].encode("utf-8")
            return state
        except KeyError:
            return False

    def get_description(self, name):
        properties = self._get_unit_properties(name, self.UNIT_INTERFACE)

        if properties is  None:
            return False

        try:
            description = properties["Description"]
            return description
        except dbus.exceptions.DBusException as error:
            print(error)
            return False

    def get_enabled_state(self, name):
        return self._get_unit_file_state(name)

    def get_error(self, name):
        service_properties = self._get_unit_properties(name, self.SERVICE_UNIT_INTERFACE)

        if service_properties is None:
            return None

        return self._get_exec_status(service_properties)

    # gets a list of all the service names in string form
    def get_str_list_all(self):
        list_service = []
        list_all = self._list_all()

        for unit in list_all:

            if unit[0].endswith("@.service"):
                continue

            if unit[0].endswith(".service"):
                split_list=unit[0].split('/')
                target=split_list[len(split_list)-1]
                list_service.append(target)
        return list_service

    def restart(self, name, mode="replace"):
        interface = self._get_interface()

        if interface is None:
            return False

        try:
            interface.RestartUnit(name, mode)
            return True
        except dbus.exceptions.DBusException as error:
            print(error)
            return False

    def start(self, name, mode="replace"):
        interface = self._get_interface()

        if interface is None:
            return False

        try:
            interface.StartUnit(name, mode)
            return True
        except dbus.exceptions.DBusException as error:
            print(error)
            return False

    def stop(self, name, mode="replace"):
        interface = self._get_interface()

        if interface is None:
            return False

        try:
            interface.StopUnit(name, mode)
            return True
        except dbus.exceptions.DBusException as error:
            print(error)
            return False


    def _list_all(self):
        interface = self._get_interface()
        re = interface.ListUnitFiles()
        return re

    def _get_unit_file_state(self, name):
        interface = self._get_interface()

        if interface is None:
            return None

        try:
            state = interface.GetUnitFileState(name)
            return state
        except dbus.exceptions.DBusException as error:
            print(error)
            return False

    def _get_interface(self):
        try:
            obj = self.__bus.get_object("org.freedesktop.systemd1", "/org/freedesktop/systemd1")
            return dbus.Interface(obj, "org.freedesktop.systemd1.Manager")
        except dbus.exceptions.DBusException as error:
            print(error)
            return None

    def _get_exec_status(self, properties):
        try:
            exec_status = int(properties["ExecMainStatus"])
            return exec_status
        except KeyError:
            return None

    def _get_result(self, properties):
        try:
            result = properties["Result"].encode("utf-8")
            return result
        except KeyError:
            return False

    def _get_unit_properties(self, name, unit_interface):
        interface = self._get_interface()

        if interface is None:
            return None

        try:
            unit_path = interface.LoadUnit(name)
            obj = self.__bus.get_object("org.freedesktop.systemd1", unit_path)
            properties_interface = dbus.Interface(obj, "org.freedesktop.DBus.Properties")
            return properties_interface.GetAll(unit_interface)
        except dbus.exceptions.DBusException as error:
            print(error)
            return None


class Service(object):
    def __init__(self, name):
        self.name = name
