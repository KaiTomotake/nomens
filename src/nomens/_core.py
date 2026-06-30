import typing
import contextlib
import collections.abc

_SENTINEL = object()

def _type_getattr[T](cls: type[T], name: str, /, default: typing.Any = _SENTINEL) -> typing.Any:
    """
    Internal helper function.

    Retrieves an attribute from the class object itself using
    `type.__getattribute__`. Used when you want to access an attribute
    without going through `_namespace_meta.__getattribute__`'s private
    attribute check, etc.

    ###  Args
    - `cls`: The class from which to retrieve the attribute.
    - `name`: The name of the attribute to retrieve.
    - `default`: The value to return if the attribute does not exist. If omitted, raises `AttributeError`.

    ### Returns
    The retrieved attribute value, or `default` if it was specified.
    """
    
    try:
        return type.__getattribute__(cls, name)
    except AttributeError:
        if default is _SENTINEL:
            raise
        return default

def _type_setattr(cls: type, name: str, value: typing.Any) -> None:
    """
    Internal helper function.

    Sets an attribute on the class object itself using
    `type.__setattr__`. Used when you want to set an attribute
    without going through `_namespace_meta.__setattr__`'s frozen
    check, etc.

    ### Args
    - `cls`: The class on which to set the attribute.
    - `name`: The name of the attribute to set.
    - `value`: The value to set.
    """

    return type.__setattr__(cls, name, value)

class _namespace_dict[V](dict[str, V]):
    """
    Internal helper class.

    Unlike a regular `dict`, raises `ValueError` if `__setitem__` is
    called for a key that already exists (i.e., if an attribute with
    the same name is defined twice within the class body).
    """
    
    def __setitem__(self, key: str, value: V) -> None:
        if key in self:
            raise ValueError(f"Duplicate name {key} in namespace {self["__qualname__"]}")
        return super().__setitem__(key, value)

class _namespace_meta(type):
    """
    Internal helper class.

    Functions as the metaclass for classes that inherit from `namespace`
    (namespace classes), enforcing the following controls on the class
    body:
    - Prohibits instantiation via `()`.
    - Prohibits normal access to attributes registered in `_ns_private`.
    - If `_ns_frozen` is `True`, prohibits assignment to or deletion of
      attributes not included in `_ns_unfrozen_attrs`.
    """

    def __call__(self, *_args, **_kwds) -> typing.Never:
        """
        Since a namespace does not need to have instances, calling `()`
        always raises `TypeError`.
        """

        raise TypeError(f"namespace {self.__qualname__} is not intended to be instantiated.")
    
    def __getattribute__(self, name: str) -> typing.Any:
        """
        On attribute access, prohibits access to private attributes
        (those registered in `_ns_private`).

        ### Args
        - `name`: The name of the attribute being accessed.

        ### Returns
        If it is not a private attribute, returns the attribute value
        as normal.

        ### Raises
        `AttributeError` if access to a private attribute is attempted.
        """

        if name in _type_getattr(type(self), "_ns_private", []):
            raise AttributeError(f"{self.__qualname__} has no public attribute {name}.")
        return super().__getattribute__(name)

    def __setattr__(self, name: str, value: typing.Any) -> None:
        """
        On attribute assignment, if frozen (`_ns_frozen` is `True`),
        prohibits assignment to attributes not included in
        `_ns_unfrozen_attrs`.

        ### Args
        - `name`: The name of the attribute being assigned.
        - `value`: The value being assigned.

        ### Raises
        If frozen and the target attribute is not unfrozen, raises
        `AttributeError` indicating that the attribute cannot be added
        (for a new attribute) or cannot be assigned to (for an existing
        attribute).
        """

        if (
            _type_getattr(type(self), "_ns_frozen", False)
            and name not in _type_getattr(type(self), "_ns_unfrozen_attrs", [])
            and name != "_ns_frozen"
            and name != "_ns_unfrozen_attrs"
            and name != "_ns_private"
        ):
            try:
                _type_getattr(type(self), name)
            except AttributeError:   
                raise AttributeError(f"Cannot add {name} to namespace '{self.__qualname__}'")
            else:
                raise AttributeError(f"Cannot assign to {name} in namespace {self.__qualname__}")
        return super().__setattr__(name, value)

    def __delattr__(self, name: str) -> None:
        """
        On attribute deletion, if frozen (`_ns_frozen` is `True`),
        prohibits deletion of attributes not included in
        `_ns_unfrozen_attrs`.

        ### Args
        - `name`: The name of the attribute being deleted.

        ### Raises
        `AttributeError` if frozen and the target attribute is not
        unfrozen.
        """

        if (
            _type_getattr(type(self), "_ns_frozen", False) 
            and name not in _type_getattr(type(self), "_ns_unfrozen_attrs", [])
        ):
            raise AttributeError(f"cannot delete {name} from frozen namespace {self.__qualname__}")
        return super().__delattr__(name)
    
    @classmethod
    def __prepare__(metacls, _name: str, _bases: tuple[type, ...], /, **_kwds) -> _namespace_dict[object]:
        """
        Uses `_namespace_dict`, which can detect duplicate definitions,
        as the namespace for the class body.

        ### Returns
        An empty `_namespace_dict` instance.
        """

        return _namespace_dict()

class namespace(metaclass=_namespace_meta):
    """
    A class that can be inherited directly to create a namespace.

    `namespace` can be customized with the following class arguments:
    - `frozen: bool = True`
    - `unfrozen_attrs: Sequence[str] | None = None`
    - `priv_attrs: Sequence[str] | None = None`

    If `frozen` is `True`, adding, editing, and deleting attributes is
    prohibited. It defaults to `True`.
    `unfrozen_attrs` expects an array of attribute names that remain
    editable even when `frozen` is `True`.
    `priv_attrs` expects an array of private attribute names.
    """

    def __init_subclass__(
            cls, *, frozen = True, 
            unfrozen_attrs: collections.abc.Sequence[str] | None = None,
            priv_attrs: collections.abc.Sequence[str] | None = None
        ) -> None:
        """
        Called when a subclass inheriting from `namespace` is defined,
        and performs the initial setup of the frozen setting, the set
        of unfreeze-eligible attributes, and the private attributes.

        ### Args
        - `frozen`: Whether to prohibit adding, editing, and deleting
          attributes. Defaults to `True`.
        - `unfrozen_attrs`: A list of attribute names to keep operable
          even when `frozen` is `True`.
        - `priv_attrs`: A list of attribute names to hide from normal
          attribute access.

        ### Raises
        `TypeError` if the class does not directly inherit from
        `namespace` (i.e., multi-level inheritance).
        """

        if unfrozen_attrs is None:
            unfrozen_attrs = []
        else:
            unfrozen_attrs = list(unfrozen_attrs)
        if priv_attrs is None:
            priv_attrs = []
        else:
            priv_attrs = list(priv_attrs)
        if namespace not in cls.__bases__:
            raise TypeError(f"namespace {cls.__qualname__} does not directly inherit from namespace. Direct inheritance is recommended.")
        try:
            _type_getattr(cls, "_ns_frozen")
        except AttributeError:
            _type_setattr(cls, "_ns_frozen", frozen)
        try:
            _type_getattr(cls, "_ns_unfrozen_attrs")
        except AttributeError:
            _type_setattr(cls, "_ns_unfrozen_attrs", unfrozen_attrs)
        try:
            _type_getattr(cls, "_ns_private")
        except AttributeError:
            _type_setattr(cls, "_ns_private", priv_attrs)
        return super().__init_subclass__()

    @classmethod
    @contextlib.contextmanager
    def unfrozen(cls, *args: str) -> collections.abc.Generator[type[typing.Self], None, None]:
        """
        A function to be used together with `with` to allow operating
        on the attributes of a class whose `frozen` is `True`, only
        within that scope.

        ### Args
        - If no arguments are given: unfreezes all attributes.
        - If one or more attribute names are given: unfreezes only
          those attributes.

        ### Yields
        The namespace itself.

        ### Note
        Upon exiting the `with` block, the frozen state (or the list of
        unfreeze-eligible attributes) is automatically restored to the
        state it was in before the call.
        """

        if len(args) != 0:
            current = _type_getattr(cls, "_ns_unfrozen_attrs", [])
            _type_setattr(cls, "_ns_unfrozen_attrs", current + [*args])
            try:
                yield cls
            finally:
                _type_setattr(cls, "_ns_unfrozen_attrs", current)
        else:
            current = _type_getattr(cls, "_ns_frozen", False)
            _type_setattr(cls, "_ns_frozen", False)
            try:
                yield cls
            finally:
                _type_setattr(cls, "_ns_frozen", current)
    
    @classmethod
    def is_frozen(cls) -> bool:
        """
        Gets whether this namespace is currently frozen.

        ### Returns
        `True` if frozen, `False` otherwise.
        """

        return _type_getattr(cls, "_ns_frozen", False)
    
    @classmethod
    def unfrozen_attrs(cls) -> list[str]:
        """
        Gets the list of attributes that can be created, edited, or
        deleted even while this namespace is frozen.

        ### Returns
        An array of attribute names.
        """

        return list(_type_getattr(cls, "_ns_unfrozen_attrs", []))

    @classmethod
    def private_attrs(cls) -> list[str]:
        """
        Gets the list of attributes in this namespace that are hidden
        from normal attribute access.

        ### Returns
        An array of attribute names.
        """
        
        return list(_type_getattr(cls, "_ns_private", []))
