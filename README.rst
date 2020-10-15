=========
 Pinject
=========

.. image:: https://badge.fury.io/py/pinject.svg
    :target: https://pypi.org/project/pinject/
.. image:: https://github.com/google/pinject/workflows/PyPI/badge.svg
    :target: https://github.com/google/pinject/actions?query=workflow%3APyPI
.. image:: https://pepy.tech/badge/pinject
    :target: https://pepy.tech/badge/pinject
.. image:: https://pepy.tech/badge/pinject/month
    :target: https://pepy.tech/badge/pinject

Pinject is a dependency injection library for python.

The primary goal of Pinject is to help you assemble objects into graphs in an
easy, maintainable way.

If you are already familiar with other dependency injection libraries, you may
want to read the condensed summary section at the end, so that you get an idea
of what Pinject is like and how it might differ from libraries you're used to.

There is a changelog of differences between released versions near the end of
this README.

Why Pinject?
============

If you're wondering why to use a dependency injection library at all: if
you're writing a lot of object-oriented code in python, then it will make your
life easier.  See, for instance:

* https://en.wikipedia.org/wiki/Dependency_injection
* http://lmgtfy.com/?q=dependency+injection

If you're wondering why to use Pinject instead of another python dependency
injection library, a few of reasons are:

* Pinject is much easier to get started with.  Forget having to decorate your code with ``@inject_this`` and ``@annotate_that`` just to get started.  With Pinject, you call ``new_object_graph()``, one line, and you're good to go.
* Pinject is a *pythonic* dependency injection library.  Python ports of other libraries, like Spring or Guice, retain the feel (and verbosity) of being designed for a statically typed language.  Pinject is designed from the ground up for python.
* The design choices in Pinject are informed by several dependency injection experts working at Google, based on many years of experience.  Several common confusing or misguided features are omitted altogether from Pinject.
* Pinject has great error messages.  They tell you exactly what you did wrong, and exactly where.  This should be a welcome change from other dependency frameworks, with their voluminous and yet inscrutable stack traces.

Look at the simplest getting-started examples for Pinject and for other
similar libraries.  Pinject should be uniformly easier to use, clearer to
read, and less boilerplate that you need to add.  If you don't find this to be
the case, email!

Installation
============

The easiest way to install Pinject is to get the latest released version from
PyPI:

.. code-block:: shell

    sudo pip install pinject

If you are interested in the developing version, you can install the next version from Test PyPI:

.. code-block:: shell

    sudo pip install \
        --no-deps \
        --no-cache \
        --upgrade \
        --index-url https://test.pypi.org/simple/ \
        pinject

You can also check out all the source code, including tests, designs, and
TODOs:

.. code-block:: shell

   git clone https://github.com/google/pinject

Basic dependency injection
==========================

The most important function in the ``pinject`` module is
``new_object_graph()``.  This creates an ``ObjectGraph``, which you can use to
instantiate objects using dependency injection.  If you pass no args to
``new_object_graph()``, it will return a reasonably configured default
``ObjectGraph``.

.. code-block:: python

    >>> class OuterClass(object):
    ...     def __init__(self, inner_class):
    ...         self.inner_class = inner_class
    ...
    >>> class InnerClass(object):
    ...     def __init__(self):
    ...         self.forty_two = 42
    ...
    >>> obj_graph = pinject.new_object_graph()
    >>> outer_class = obj_graph.provide(OuterClass)
    >>> print outer_class.inner_class.forty_two
    42
    >>>

As you can see, you don't need to tell Pinject how to construct its
``ObjectGraph``, and you don't need to put decorators in your code.  Pinject has
reasonable defaults that allow it to work out of the box.

A Pinject *binding* is an association between an *arg name* and a *provider*.
In the example above, Pinject created a binding between the arg name
``inner_class`` and an implicitly created provider for the class
``InnerClass``.  The binding it had created was how Pinject knew that it
should pass an instance of ``InnerClass`` as the value of the ``inner_class``
arg when instantiating ``OuterClass``.

Implicit class bindings
=======================

Pinject creates implicit bindings for classes.  The implicit bindings assume
your code follows PEP8 conventions: your classes are named in ``CamelCase``,
and your args are named in ``lower_with_underscores``.  Pinject transforms
class names to injectable arg names by lowercasing words and connecting them
with underscores.  It will also ignore any leading underscore on the class
name.

+-------------+-------------+
| Class name  | Arg name    |
+=============+=============+
| ``Foo``     | ``foo``     |
+-------------+-------------+
| ``FooBar``  | ``foo_bar`` |
+-------------+-------------+
| ``_Foo``    | ``foo``     |
+-------------+-------------+
| ``_FooBar`` | ``foo_bar`` |
+-------------+-------------+

If two classes map to the same arg name, whether those classes are in the same
module or different modules, Pinject will not create an implicit binding for
that arg name (though it will not raise an error).

Finding classes and providers for implicit bindings
===================================================

So far, the examples have not told ``new_object_graph()`` the classes for
which it should create implicit bindings.  ``new_object_graph()`` by default
looks in all imported modules, but you may occasionally want to restrict the
classes for which ``new_object_graph()`` creates implicit bindings.  If so,
``new_object_graph()`` has two args for this purpose.

* The ``modules`` arg specifies in which (python) modules to look for classes; this defaults to ``ALL_IMPORTED_MODULES``.
* The ``classes`` arg specifies a exact list of classes; this defaults to ``None``.

.. code-block:: python

    >>> class SomeClass(object):
    ...     def __init__(self, foo):
    ...         self.foo = foo
    ...
    >>> class Foo(object):
    ...     pass
    ...
    >>> obj_graph = pinject.new_object_graph(modules=None, classes=[SomeClass])
    >>> # obj_graph.provide(SomeClass)  # would raise a NothingInjectableForArgError
    >>> obj_graph = pinject.new_object_graph(modules=None, classes=[SomeClass, Foo])
    >>> some_class = obj_graph.provide(SomeClass)
    >>>

Auto-copying args to fields
===========================

One thing that can get tedious about dependency injection via initializers is
that you need to write ``__init__()`` methods that copy args to fields.  These
``__init__()`` methods can get repetitive, especially when you have several
initializer args.

.. code-block:: python

    >>> class ClassWithTediousInitializer(object):
    ...     def __init__(self, foo, bar, baz, quux):
    ...         self._foo = foo
    ...         self._bar = bar
    ...         self._baz = baz
    ...         self._quux = quux
    ...
    >>>

Pinject provides decorators that you can use to avoid repetitive initializer
bodies.

* ``@copy_args_to_internal_fields`` prepends an underscore, i.e., it copies an arg named ``foo`` to a field named ``_foo``.  It's useful for normal classes.
* ``@copy_args_to_public_fields`` copies the arg named as-is, i.e., it copies an arg named ``foo`` to a field named ``foo``.  It's useful for data objects.

.. code-block:: python

    >>> class ClassWithTediousInitializer(object):
    ...     @pinject.copy_args_to_internal_fields
    ...     def __init__(self, foo, bar, baz, quux):
    ...         pass
    ...
    >>> cwti = ClassWithTediousInitializer('a-foo', 'a-bar', 'a-baz', 'a-quux')
    >>> print cwti._foo
    'a-foo'
    >>>

When using these decorators, you'll normally ``pass`` in the body of the
initializer, but you can put other statements there if you need to.  The args
will be copied to fields before the initializer body is executed.

These decorators can be applied to initializers that take ``**kwargs`` but not
initializers that take ``*pargs`` (since it would be unclear what field name
to use).

Binding specs
=============

To create any bindings more complex than the implicit class bindings described
above, you use a *binding spec*.  A binding spec is any python class that
inherits from ``BindingSpec``.  A binding spec can do three things:

* Its ``configure()`` method can create explicit bindings to classes or instances, as well as requiring bindings without creating them.
* Its ``dependencies()`` method can return depended-on binding specs.
* It can have provider methods, for which explicit bindings are created.

The ``new_object_graph()`` function takes a sequence of binding spec instances
as its ``binding_specs`` arg.  ``new_object_graph()`` takes binding spec
instances, rather than binding spec classes, so that you can manually inject
any initial dependencies into the binding specs as needed.

Binding specs should generally live in files named ``binding_specs.py``, where
each file is named in the plural even if there is exactly one binding spec in
it.  Ideally, a directory's worth of functionality should be coverable with a
single binding spec.  If not, you can create multiple binding specs in the
same ``binding_specs.py`` file.  If you have so many binding specs that you
need to split them into multiple files, you should name them each with a
``_binding_specs.py`` suffix.

Binding spec ``configure()`` methods
------------------------------------

Pinject creates implicit bindings for classes, but sometimes the implicit
bindings aren't what you want.  For instance, if you have
``SomeReallyLongClassName``, you may not want to name your initializer args
``some_really_long_class_name`` but instead use something shorter like
``long_name``, just for this class.

For such situations, you can create explicit bindings using the
``configure()`` method of a binding spec.  The ``configure()`` method takes a
function ``bind()`` as an arg and calls that function to create explicit
bindings.

.. code-block:: python

    >>> class SomeClass(object):
    ...     def __init__(self, long_name):
    ...         self.long_name = long_name
    ...
    >>> class SomeReallyLongClassName(object):
    ...     def __init__(self):
    ...         self.foo = 'foo'
    ...
    >>> class MyBindingSpec(pinject.BindingSpec):
    ...     def configure(self, bind):
    ...         bind('long_name', to_class=SomeReallyLongClassName)
    ...
    >>> obj_graph = pinject.new_object_graph(binding_specs=[MyBindingSpec()])
    >>> some_class = obj_graph.provide(SomeClass)
    >>> print some_class.long_name.foo
    'foo'
    >>>

The ``bind()`` function passed to a binding function binds its first arg,
which must be an arg name (as a ``str``), to exactly one of two kinds of
things.

* Using ``to_class`` binds to a class.  When the binding is used, Pinject injects an instance of the class.
* Using ``to_instance`` binds to an instance of some object.  Every time the binding is used, Pinject uses that instance.

.. code-block:: python

    >>> class SomeClass(object):
    ...     def __init__(self, foo):
    ...         self.foo = foo
    ...
    >>> class MyBindingSpec(pinject.BindingSpec):
    ...     def configure(self, bind):
    ...         bind('foo', to_instance='a-foo')
    ...
    >>> obj_graph = pinject.new_object_graph(binding_specs=[MyBindingSpec()])
    >>> some_class = obj_graph.provide(SomeClass)
    >>> print some_class.foo
    'a-foo'
    >>>

The ``configure()`` method of a binding spec also may take a function
``require()`` as an arg and use that function to require that a binding be
present without actually defining that binding.  ``require()`` takes as args
the name of the arg for which to require a binding.

.. code-block:: python

    >>> class MainBindingSpec(pinject.BindingSpec):
    ...     def configure(self, require):
    ...         require('foo')
    ...
    >>> class RealFooBindingSpec(pinject.BindingSpec):
    ...     def configure(self, bind):
    ...         bind('foo', to_instance='a-real-foo')
    ...
    >>> class StubFooBindingSpec(pinject.BindingSpec):
    ...     def configure(self, bind):
    ...         bind('foo', to_instance='a-stub-foo')
    ...
    >>> class SomeClass(object):
    ...     def __init__(self, foo):
    ...         self.foo = foo
    ...
    >>> obj_graph = pinject.new_object_graph(
    ...     binding_specs=[MainBindingSpec(), RealFooBindingSpec()])
    >>> some_class = obj_graph.provide(SomeClass)
    >>> print some_class.foo
    'a-real-foo'
    >>> # pinject.new_object_graph(
    ... #    binding_specs=[MainBindingSpec()])  # would raise a MissingRequiredBindingError
    ...
    >>>

Being able to require a binding without defining the binding is useful when
you know the code will need some dependency satisfied, but there is more than
one implementation that satisfies that dependency, e.g., there may be a real
RPC client and a fake RPC client.  Declaring the dependency means that any
expected but missing bindings will be detected early, when
``new_object_graph()`` is called, rather than in the middle of running your
program.

You'll notice that the ``configure()`` methods above have different
signatures, sometimes taking the arg ``bind`` and sometimes taking the arg
``require``.  ``configure()`` methods must take at least one arg that is
either ``bind`` or ``require``, and they may have both args.  Pinject will
pass whichever arg or args your ``configure()`` method needs.

Binding spec dependencies
-------------------------

Binding specs can declare dependencies.  A binding spec declares its
dependencies by returning a sequence of instances of the dependent binding
specs from its ``dependencies()`` method.

.. code-block:: python

    >>> class ClassOne(object):
    ...    def __init__(self, foo):
    ...        self.foo = foo
    ...
    >>> class BindingSpecOne(pinject.BindingSpec):
    ...     def configure(self, bind):
    ...         bind('foo', to_instance='foo-')
    ...
    >>> class ClassTwo(object):
    ...     def __init__(self, class_one, bar):
    ...         self.foobar = class_one.foo + bar
    ...
    >>> class BindingSpecTwo(pinject.BindingSpec):
    ...     def configure(self, bind):
    ...         bind('bar', to_instance='-bar')
    ...     def dependencies(self):
    ...         return [BindingSpecOne()]
    ...
    >>> obj_graph = pinject.new_object_graph(binding_specs=[BindingSpecTwo()])
    >>> class_two = obj_graph.provide(ClassTwo)
    >>> print class_two.foobar
    'foo--bar'
    >>>

If classes from module A are injected as collaborators into classes from
module B, then you should consider having the binding spec for module B depend
on the binding spec for module A.  In the example above, ``ClassOne`` is
injected as a collaborator into ``ClassTwo``, and so ``BindingSpecTwo`` (the
binding spec for ``ClassTwo``) depends on ``BindingSpecOne`` (the binding spec
for ``ClassOne``).

In this way, you can build a graph of binding spec dependencies that mirrors
the graph of collaborator dependencies.

Since explicit bindings cannot conflict (see the section below on binding
precedence), a binding spec should only have dependencies that there will
never be a choice about using.  If there may be a choice, then it is better to
list the binding specs separately and explicitly when calling
``new_object_graph()``.

The binding spec dependencies can be a directed acyclic graph (DAG); that is,
binding spec A can be a dependency of B and of C, and binding spec D can have
dependencies on B and C.  Even though there are multiple dependency paths from
D to A, the bindings in binding spec A will only be evaluated once.

The binding spec instance of A that is a dependency of B is considered the
same as the instance that is a dependency of C if the two instances are equal
(via ``__eq__()``).  The default implementation of ``__eq__()`` in
``BindingSpec`` says that two binding specs are equal if they are of exactly
the same python type.  You will need to override ``__eq__()`` (as well as
``__hash__()``) if your binding spec is parameterized, i.e., if it takes one
or more initializer args so that two instances of the binding spec may behave
differently.

.. code-block:: python

    >>> class SomeBindingSpec(pinject.BindingSpec):
    ...     def __init__(self, the_instance):
    ...         self._the_instance = the_instance
    ...     def configure(self, bind):
    ...         bind('foo', to_instance=self._the_instance)
    ...     def __eq__(self, other):
    ...         return (type(self) == type(other) and
    ...                 self._the_instance == other._the_instance)
    ...     def __hash__(self):
    ...         return hash(type(self)) ^ hash(self._the_instance)
    ...
    >>>

Provider methods
----------------

If it takes more to instantiate a class than calling its initializer and
injecting initializer args, then you can write a *provider method* for it.
Pinject can use provider methods to instantiate objects used to inject as the
values of other args.

Pinject looks on binding specs for methods named like provider methods and
then creates explicit bindings for them.

.. code-block:: python

    >>> class SomeClass(object):
    ...     def __init__(self, foo):
    ...         self.foo = foo
    ...
    >>> class SomeBindingSpec(pinject.BindingSpec):
    ...     def provide_foo(self):
    ...         return 'some-complex-foo'
    ...
    >>> obj_graph = pinject.new_object_graph(binding_specs=[SomeBindingSpec()])
    >>> some_class = obj_graph.provide(SomeClass)
    >>> print some_class.foo
    'some-complex-foo'
    >>>

Pinject looks on binding specs for methods whose names start with
``provide_``, and it assumes that the methods are providers for whatever the
rest of their method names are.  For instance, Pinject assumes that the method
``provide_foo_bar()`` is a provider method for the arg name ``foo_bar``.

Pinject injects all args of provider methods that have no default when it
calls the provider method.

.. code-block:: python

    >>> class SomeClass(object):
    ...     def __init__(self, foobar):
    ...         self.foobar = foobar
    ...
    >>> class SomeBindingSpec(pinject.BindingSpec):
    ...     def provide_foobar(self, bar, hyphen='-'):
    ...         return 'foo' + hyphen + bar
    ...     def provide_bar(self):
    ...         return 'bar'
    ...
    >>> obj_graph = pinject.new_object_graph(binding_specs=[SomeBindingSpec()])
    >>> some_class = obj_graph.provide(SomeClass)
    >>> print some_class.foobar
    'foo-bar'
    >>>

Binding precedence
==================

Bindings have precedence: explicit bindings take precedence over implicit
bindings.

* Explicit bindings are the bindings that come from binding specs.
* Implicit bindings are the bindings created for classes in the ``modules`` and ``classes`` args passed to ``new_object_graph()``.

Pinject will prefer an explicit to an implicit binding.

.. code-block:: python

    >>> class SomeClass(object):
    ...     def __init__(self, foo):
    ...         self.foo = foo
    ...
    >>> class Foo(object):
    ...     pass
    ...
    >>> class SomeBindingSpec(pinject.BindingSpec):
    ...     def configure(self, bind):
    ...         bind('foo', to_instance='foo-instance')
    ...
    >>> obj_graph = pinject.new_object_graph(binding_specs=[SomeBindingSpec()])
    >>> some_class = obj_graph.provide(SomeClass)
    >>> print some_class.foo
    'foo-instance'
    >>>

If you have two classes named the same thing, Pinject will have two different
(and thus conflicting) implicit bindings.  But Pinject will not complain
unless you try to use those bindings.  Pinject *will* complain if you try to
create different (and thus conflicting) explicit bindings.

Safety
======

Pinject tries to strike a balance between being helpful and being safe.
Sometimes, you may want or need to change this balance.

``new_object_graph()`` uses implicit bindings by default.  If you worry that
you may accidentally inject a class or use a provider function
unintentionally, then you can make ``new_object_graph()`` ignore implicit
bindings, by setting ``only_use_explicit_bindings=True``.  If you do so, then
Pinject will only use explicit bindings.

If you want to promote an implicit binding to be an explicit binding, you can
annotate the corresponding class with ``@inject()``.  The ``@inject()``
decorator lets you create explicit bindings without needing to create binding
specs, as long as you can live with the binding defaults (e.g., no annotations
on args, see below).

.. code-block:: python

    >>> class ExplicitlyBoundClass(object):
    ...     @pinject.inject()
    ...     def __init__(self, foo):
    ...         self.foo = foo
    ...
    >>> class ImplicitlyBoundClass(object):
    ...     def __init__(self, foo):
    ...         self.foo = foo
    ...
    >>> class SomeBindingSpec(pinject.BindingSpec):
    ...     def configure(self, bind):
    ...         bind('foo', to_instance='explicit-foo')
    ...
    >>> obj_graph = pinject.new_object_graph(binding_specs=[SomeBindingSpec()],
    ...     only_use_explicit_bindings=True)
    >>> # obj_graph.provide(ImplicitlyBoundClass)  # would raise a NonExplicitlyBoundClassError
    >>> some_class = obj_graph.provide(ExplicitlyBoundClass)
    >>> print some_class.foo
    'explicit-foo'
    >>>

You can also promote an implicit binding to explicit by using
``@annotated_arg()`` (see below), with or without ``@inject()`` as well.

(Previous versions of Pinject included an ``@injectable`` decorator.  That is
deprecated in favor of ``@inject()``.  Note that ``@inject()`` needs parens,
whereas ``@injectable`` didn't.)

On the opposite side of permissiveness, Pinject by default will complain if a
provider method returns ``None``.  If you really want to turn off this default
behavior, you can pass ``allow_injecting_none=True`` to
``new_object_graph()``.

Annotations
===========

Pinject *annotations* let you have different objects injected for the same arg
name.  For instance, you may have two classes in different parts of your
codebase named the same thing, and you want to use the same arg name in
different parts of your codebase.

On the arg side, an annotation tells Pinject only to inject using a binding
whose binding key includes the annotation object.  You can use
``@annotate_arg()`` on an initializer, or on a provider method, to specify the
annotation object.

On the binding side, an annotation changes the binding so that the key of the
binding includes the annotation object.  When using ``bind()`` in a binding
spec's ``configure()`` method, you can pass an ``annotated_with`` arg to
specify the annotation object.

.. code-block:: python

    >>> class SomeClass(object):
    ...     @pinject.annotate_arg('foo', 'annot')
    ...     def __init__(self, foo):
    ...         self.foo = foo
    ...
    >>> class SomeBindingSpec(pinject.BindingSpec):
    ...     def configure(self, bind):
    ...         bind('foo', annotated_with='annot', to_instance='foo-with-annot')
    ...         bind('foo', annotated_with=12345, to_instance='12345-foo')
    ...
    >>> obj_graph = pinject.new_object_graph(binding_specs=[SomeBindingSpec()])
    >>> some_class = obj_graph.provide(SomeClass)
    >>> print some_class.foo
    'foo-with-annot'
    >>>

Also on the binding side, when defining a provider method, you can use the
``@provides()`` decorator.  The decorator lets you pass an ``annotated_with``
arg to specify the annotation object.  The decorator's first param,
``arg_name`` also lets you override what arg name you want the provider to be
for.  This is optional but useful if you want the same binding spec to have
two provider methods for the same arg name but annotated differently.
(Otherwise, the methods would need to be named the same, since they're for the
same arg name.)

.. code-block:: python

    >>> class SomeClass(object):
    ...     @pinject.annotate_arg('foo', 'annot')
    ...     def __init__(self, foo):
    ...         self.foo = foo
    ...
    >>> class SomeBindingSpec(pinject.BindingSpec):
    ...     @pinject.provides('foo', annotated_with='annot')
    ...     def provide_annot_foo(self):
    ...         return 'foo-with-annot'
    ...     @pinject.provides('foo', annotated_with=12345)
    ...     def provide_12345_foo(self):
    ...         return '12345-foo'
    ...
    >>> obj_graph = pinject.new_object_graph(binding_specs=[SomeBindingSpec()])
    >>> some_class = obj_graph.provide(SomeClass)
    >>> print some_class.foo
    'foo-with-annot'
    >>>

When requiring a binding, via the ``require`` arg passed into the
``configure()`` method of a binding spec, you can pass the arg
``annotated_with`` to require an annotated binding.

.. code-block:: python

    >>> class MainBindingSpec(pinject.BindingSpec):
    ...     def configure(self, require):
    ...         require('foo', annotated_with='annot')
    ...
    >>> class NonSatisfyingBindingSpec(pinject.BindingSpec):
    ...     def configure(self, bind):
    ...         bind('foo', to_instance='an-unannotated-foo')
    ...
    >>> class SatisfyingBindingSpec(pinject.BindingSpec):
    ...     def configure(self, bind):
    ...         bind('foo', annotated_with='annot', to_instance='an-annotated-foo')
    ...
    >>> obj_graph = pinject.new_object_graph(
    ...     binding_specs=[MainBindingSpec(), SatisfyingBindingSpec()])  # works
    >>> # obj_graph = pinject.new_object_graph(
    ... #     binding_specs=[MainBindingSpec(),
    ... #                    NonSatisfyingBindingSpec()])  # would raise a MissingRequiredBindingError
    >>>

You can use any kind of object as an annotation object as long as it
implements ``__eq__()`` and ``__hash__()``.

Scopes
======

By default, Pinject remembers the object it injected into a (possibly
annotated) arg, so that it can inject the same object into other args with the
same name.  This means that, for each arg name, a single instance of the
bound-to class, or a single instance returned by a provider method, is created
by default.

.. code-block:: python

    >>> class SomeClass(object):
    ...     def __init__(self, foo):
    ...         self.foo = foo
    ...
    >>> class SomeBindingSpec(pinject.BindingSpec):
    ...     def provide_foo(self):
    ...         return object()
    ...
    >>> obj_graph = pinject.new_object_graph(binding_specs=[SomeBindingSpec()])
    >>> some_class_1 = obj_graph.provide(SomeClass)
    >>> some_class_2 = obj_graph.provide(SomeClass)
    >>> print some_class_1.foo is some_class_2.foo
    True
    >>>

In some cases, you may want to create new instances, always or sometimes,
instead of reusing them each time they're injected.  If so, you want to use
*scopes*.

A scope controls memoization (i.e., caching).  A scope can choose to cache
never, sometimes, or always.

Pinject has two built-in scopes.  *Singleton scope* (``SINGLETON``) is the
default and always caches.  *Prototype scope* (``PROTOTYPE``) is the other
built-in option and does no caching whatsoever.

Every binding is associated with a scope.  You can specify a scope for a
binding by decorating a provider method with ``@in_scope()``, or by passing an
``in_scope`` arg to ``bind()`` in a binding spec's ``configure()`` method.

.. code-block:: python

    >>> class SomeClass(object):
    ...     def __init__(self, foo):
    ...         self.foo = foo
    ...
    >>> class SomeBindingSpec(pinject.BindingSpec):
    ...     @pinject.provides(in_scope=pinject.PROTOTYPE)
    ...     def provide_foo(self):
    ...         return object()
    ...
    >>> obj_graph = pinject.new_object_graph(binding_specs=[SomeBindingSpec()])
    >>> some_class_1 = obj_graph.provide(SomeClass)
    >>> some_class_2 = obj_graph.provide(SomeClass)
    >>> print some_class_1.foo is some_class_2.foo
    False
    >>>

If a binding specifies no scope explicitly, then it is in singleton scope.
Implicit class bindings are always in singleton scope.

Memoization of class bindings works at the class level, not at the binding key
level.  This means that, if you bind two arg names (or the same arg name with
two different annotations) to the same class, and the class is in a memoizing
scope, then the same class instance will be provided when you inject the
different arg names.

.. code-block:: python

    >>> class InjectedClass(object):
    ...     pass
    ...
    >>> class SomeObject(object):
    ...     def __init__(self, foo, bar):
    ...         self.foo = foo
    ...         self.bar = bar
    ...
    >>> class SomeBindingSpec(pinject.BindingSpec):
    ...     def configure(self, bind):
    ...         bind('foo', to_class=InjectedClass)
    ...         bind('bar', to_class=InjectedClass)
    ...
    >>> obj_graph = pinject.new_object_graph(
    ...     binding_specs=[SomeBindingSpec()])
    >>> some_object = obj_graph.provide(SomeObject)
    >>> print some_object.foo is some_object.bar
    True
    >>>

Pinject memoizes class bindings this way because this is more likely to be
what you mean if you bind two different arg names to the same class in
singleton scope: you want only one instance of the class, even though it may
be injected in multiple places.

Provider bindings
=================

Sometimes, you need to inject not just a single instance of some class, but
rather you need to inject the ability to create instances on demand.
(Clearly, this is most useful when the binding you're using is not in the
singleton scope, otherwise you'll always get the same instance, and you may as
well just inject that..)

You could inject the Pinject object graph, but you'd have to do that
dependency injection manually (Pinject doesn't inject itself!), and you'd be
injecting a huge set of capabilities when your class really only needs to
instantiate objects of one type.

To solve this, Pinject creates *provider bindings* for each bound arg name.
It will look at the arg name for the prefix ``provide_``, and if it finds that
prefix, it assumes you want to inject a provider function for whatever the
rest of the arg name is.  For instance, if you have an arg named
``provide_foo_bar``, then Pinject will inject a zero-arg function that, when
called, provides whatever the arg name ``foo_bar`` is bound to.

.. code-block:: python

    >>> class Foo(object):
    ...   def __init__(self):
    ...     self.forty_two = 42
    ...
    >>> class SomeBindingSpec(pinject.BindingSpec):
    ...     def configure(self, bind):
    ...         bind('foo', to_class=Foo, in_scope=pinject.PROTOTYPE)
    ...
    >>> class NeedsProvider(object):
    ...     def __init__(self, provide_foo):
    ...         self.provide_foo = provide_foo
    ...
    >>> obj_graph = pinject.new_object_graph(binding_specs=[SomeBindingSpec()])
    >>> needs_provider = obj_graph.provide(NeedsProvider)
    >>> print needs_provider.provide_foo() is needs_provider.provide_foo()
    False
    >>> print needs_provider.provide_foo().forty_two
    42
    >>>

Pinject will always look for the ``provide_`` prefix as a signal to inject a
provider function, anywhere it injects dependencies (initializer args, binding
spec provider methods, etc.).  This does mean that it's quite difficult, say,
to inject an instance of a class named ``ProvideFooBar`` into an arg named
``provide_foo_bar``, but assuming you're naming your classes as noun phrases
instead of verb phrases, this shouldn't be a problem.

Watch out: don't confuse

* *provider bindings*, which let you inject args named ``provide_something`` with provider functions; and
* *provider methods*, which are methods of binding specs that provide instances of some arg name.

Partial injection
=================

Provider bindings are useful when you want to create instances of a class on
demand.  But a zero arg provider function will always return an instance
configured the same way (within a given scope).  Sometimes, you want the
ability to parameterize the provided instances, e.g., based on run-time user
configuration.  You want the ability to create instances where part of the
initialization data is provided per-instance at run-time and part of the
initialization data is injected as dependencies.

To do this, other dependency injection libraries have you define factory
classes.  You inject dependencies into the factory class's initializer
function, and then you call the factory class's creation method with the
per-instance data.

.. code-block:: python

    >>> class WidgetFactory(object):
    ...     def __init__(self, widget_polisher):
    ...         self._widget_polisher = widget_polisher
    ...     def new(self, color):  # normally would contain some non-trivial code...
    ...         return some_function_of(self._widget_polisher, color)
    ...
    >>> class SomeBindingSpec(pinject.BindingSpec):
    ...     def provide_something_with_colored_widgets(self, colors, widget_factory):
    ...         return SomethingWithColoredWidgets(
    ...             [widget_factory.new(color) for color in colors])
    ...
    >>>

You can follow this pattern in Pinject, but it involves boring boilerplate for
the factory class, saving away the initializer-injected dependencies to be
used in the creation method.  Plus, you have to create yet another
``...Factory`` class, which makes you feel like you're programming in java,
not python.

As a less repetitive alternative, Pinject lets you use *partial injection* on
the provider functions returned by provider bindings.  You use the
``@inject()`` decorator to tell Pinject ahead of time which args you expect to
pass directly (vs. automatic injection), and then you pass those args directly
when calling the provider function.

.. code-block:: python

    >>> class SomeBindingSpec(pinject.BindingSpec):
    ...     @pinject.inject(['widget_polisher'])
    ...     def provide_widget(self, color, widget_polisher):
    ...         return some_function_of(widget_polisher, color)
    ...     def provide_something_needing_widgets(self, colors, provide_widget):
    ...         return SomethingNeedingWidgets(
    ...             [provide_widget(color) for color in colors])
    ...
    >>>

The first arg to ``@inject()``, ``arg_names``, specifies which args of the
decorated method should be injected as dependencies.  If specified, it must be
a non-empty sequence of names of the decorated method's args.  The remaining
decorated method args will be passed directly.

In the example above, note that, although there is a method called
``provide_widget()`` and an arg of ``provide_something_needing_widgets()``
called ``provide_widget``, these are not exactly the same!  The latter is a
dependency-injected wrapper around the former.  The wrapper ensures that the
``color`` arg is passed directly and then injects the ``widget_polisher``
dependency.

The ``@inject()`` decorator works to specify args passed directly both for
provider bindings to provider methods (as in the example above) and for
provider bindings to classes (where you can pass args directly to the
initializer, as in the example below).

.. code-block:: python

    >>> class Widget(object):
    ...     @pinject.inject(['widget_polisher'])
    ...     def __init__(self, color, widget_polisher):
    ...         pass  # normally something involving color and widget_polisher
    ...
    >>> class SomeBindingSpec(pinject.BindingSpec):
    ...     def provide_something_needing_widgets(self, colors, provide_widget):
    ...         return SomethingNeedingWidgets(
    ...             [provide_widget(color) for color in colors])
    ...
    >>>

The ``@inject()`` decorator also takes an ``all_except`` arg.  You can use
this, instead of the (first positional) ``arg_names`` arg, if it's clearer and
more concise to say which args are *not* injected (i.e., which args are passed
directly).

.. code-block:: python

    >>> class Widget(object):
    ...     # equivalent to @pinject.inject(['widget_polisher']):
    ...     @pinject.inject(all_except=['color'])
    ...     def __init__(self, color, widget_polisher):
    ...         pass  # normally something involving color and widget_polisher
    ...
    >>>

If both ``arg_names`` and ``all_except`` are omitted, then all args are
injected by Pinject, and none are passed directly.  (Both ``arg_names`` and
``all_except`` may not be specified at the same time.)  Wildcard positional
and keyword args (i.e., ``*pargs`` and ``**kwargs``) are always passed
directly, not injected.

If you use ``@inject()`` to mark at least one arg of a provider method (or
initializer) as passed directly, then you may no longer directly inject that
provider method's corresponding arg name.  You must instead use a provider
binding to inject a provider function, and then pass the required direct
arg(s), as in the examples above.

Custom scopes
=============

If you want to, you can create your own custom scope.  A custom scope is
useful when you have some objects that need to be reused (i.e., cached) but
whose lifetime is shorter than the entire lifetime of your program.

A custom scope is any class that implements the ``Scope`` interface.

.. code-block:: python

    class Scope(object):
        def provide(self, binding_key, default_provider_fn):
            raise NotImplementedError()

The ``binding_key`` passed to ``provide()`` will be an object implementing
``__eq__()`` and ``__hash__()`` but otherwise opaque (you shouldn't need to
introspect it).  You can think of the binding key roughly as encapsulating the
arg name and annotation (if any).  The ``default_provider_fn`` passed to
``provide()`` is a zero-arg function that, when called, provides an instance
of whatever should be provided.

The job of a scope's ``provide()`` function is to return a cached object if
available and appropriate, otherwise to return (and possibly cache) the result
of calling the default provider function.

Scopes almost always have other methods that control clearing the scope's
cache.  For instance, a scope may have "enter scope" and "exit scope" methods,
or a single direct "clear cache" method.  When passing a custom scope to
Pinject, your code should keep a handle to the custom scope and use that
handle to clear the scope's cache at the appropriate time.

You can use one or more custom scopes by passing a map from *scope identifier*
to scope as the ``id_to_scope`` arg of ``new_object_graph()``.

.. code-block:: python

    >>> class MyScope(pinject.Scope):
    ...     def __init__(self):
    ...         self._cache = {}
    ...     def provide(self, binding_key, default_provider_fn):
    ...         if binding_key not in self._cache:
    ...             self._cache[binding_key] = default_provider_fn()
    ...         return self._cache[binding_key]
    ...     def clear(self):
    ...         self._cache = {}
    ...
    >>> class SomeClass(object):
    ...     def __init__(self, foo):
    ...         self.foo = foo
    ...
    >>> class SomeBindingSpec(pinject.BindingSpec):
    ...     @pinject.provides(in_scope='my custom scope')
    ...     def provide_foo(self):
    ...         return object()
    ...
    >>> my_scope = MyScope()
    >>> obj_graph = pinject.new_object_graph(
    ...     binding_specs=[SomeBindingSpec()],
    ...     id_to_scope={'my custom scope': my_scope})
    >>> some_class_1 = obj_graph.provide(SomeClass)
    >>> some_class_2 = obj_graph.provide(SomeClass)
    >>> my_scope.clear()
    >>> some_class_3 = obj_graph.provide(SomeClass)
    >>> print some_class_1.foo is some_class_2.foo
    True
    >>> print some_class_2.foo is some_class_3.foo
    False
    >>>

A scope identifier can be any object implementing ``__eq__()`` and
``__hash__()``.

If you plan to use Pinject in a multi-threaded environment (and even if you
don't plan to now but may some day), you should make your custom scope
thread-safe.  The example custom scope above could be trivially (but more
verbosely) rewritten to be thread-safe, as in the example below.  The lock is
reentrant so that something in ``MyScope`` can be injected into something else
in ``MyScope``.

.. code-block:: python

    >>> class MyScope(pinject.Scope):
    ...     def __init__(self):
    ...         self._cache = {}
    ...         self._rlock = threading.RLock()
    ...     def provide(self, binding_key, default_provider_fn):
    ...         with self._rlock:
    ...             if binding_key not in self._cache:
    ...                 self._cache[binding_key] = default_provider_fn()
    ...             return self._cache[binding_key]
    ...     def clear(self):
    ...         with self._rlock:
    ...             self._cache = {}
    >>>

Scope accessibility
===================

To prevent yourself from injecting objects where they don't belong, you may
want to validate one object being injected into another w.r.t. scope.

For instance, you may have created a custom scope for HTTP requests handled by
your program.  Objects in request scope would be cached for the duration of a
single HTTP request.  You may want to verify that objects in request scope
never get injected into objects in singleton scope.  Such an injection is
likely not to make semantic sense, since it would make something tied to one
HTTP request be used for the duration of your program.

Pinject lets you pass a validation function as the
``is_scope_usable_from_scope`` arg to ``new_object_graph()``.  This function
takes two scope identifiers and returns ``True`` iff an object in the first
scope can be injected into an object of the second scope.

.. code-block:: python

    >>> class RequestScope(pinject.Scope):
    ...     def start_request(self):
    ...         self._cache = {}
    ...     def provide(self, binding_key, default_provider_fn):
    ...         if binding_key not in self._cache:
    ...             self._cache[binding_key] = default_provider_fn()
    ...         return self._cache[binding_key]
    ...
    >>> class SomeClass(object):
    ...     def __init__(self, foo):
    ...         self.foo = foo
    ...
    >>> class SomeBindingSpec(pinject.BindingSpec):
    ...     @pinject.provides(in_scope=pinject.SINGLETON)
    ...     def provide_foo(bar):
    ...         return 'foo-' + bar
    ...     @pinject.provides(in_scope='request scope')
    ...     def provide_bar():
    ...         return '-bar'
    ...
    >>> def is_usable(scope_id_inner, scope_id_outer):
    ...     return not (scope_id_inner == 'request scope' and
    ...                 scope_id_outer == scoping.SINGLETON)
    ...
    >>> my_request_scope = RequestScope()
    >>> obj_graph = pinject.new_object_graph(
    ...     binding_specs=[SomeBindingSpec()],
    ...     id_to_scope={'request scope': my_request_scope},
    ...     is_scope_usable_from_scope=is_usable)
    >>> my_request_scope.start_request()
    >>> # obj_graph.provide(SomeClass)  # would raise a BadDependencyScopeError
    >>>

The default scope accessibility validator allows objects from any scope to be
injected into objects from any other scope.

Changing naming conventions
===========================

If your code follows PEP8 naming coventions, then you're likely happy with the
default implicit bindings (where the class ``FooBar`` gets bound to the arg
name ``foo_bar``) and where ``provide_foo_bar()`` is a binding spec's provider
method for the arg name ``foo_bar``.

But if not, read on!

Customizing implicit bindings
-----------------------------

``new_object_graph()`` takes a ``get_arg_names_from_class_name`` arg.  This is
the function that is used to determine implicit class bindings.  This function
takes in a class name (e.g., ``FooBar``) and returns the arg names to which
that class should be implicitly bound (e.g., ``['foo_bar']``).  Its default
behavior is described in the "implicit class bindings" section above, but that
default behavior can be overridden.

For instance, suppose that your code uses a library that names many classes
with the leading letter X (e.g., ``XFooBar``), and you'd like to be able to
bind that to a corresponding arg name without the leading X (e.g.,
``foo_bar``).

.. code-block:: python

    >>> import re
    >>> def custom_get_arg_names(class_name):
    ...     stripped_class_name = re.sub('^_?X?', '', class_name)
    ...     return [re.sub('(?!^)([A-Z]+)', r'_\1', stripped_class_name).lower()]
    ...
    >>> print custom_get_arg_names('XFooBar')
    ['foo_bar']
    >>> print custom_get_arg_names('XLibraryClass')
    ['library_class']
    >>> class OuterClass(object):
    ...     def __init__(self, library_class):
    ...         self.library_class = library_class
    ...
    >>> class XLibraryClass(object):
    ...     def __init__(self):
    ...         self.forty_two = 42
    ...
    >>> obj_graph = pinject.new_object_graph(
    ...     get_arg_names_from_class_name=custom_get_arg_names)
    >>> outer_class = obj_graph.provide(OuterClass)
    >>> print outer_class.library_class.forty_two
    42
    >>>

The function passed as the ``get_arg_names_from_class_name`` arg to
``new_object_graph()`` can return as many or as few arg names as it wants.  If
it always returns the empty list (i.e., if it is ``lambda _: []``), then that
disables implicit class bindings.

Customizing binding spec method names
-------------------------------------

The standard binding spec methods to configure bindings and declare
dependencies are named ``configure`` and ``dependencies``, by default.  If you
need to, you can change their names by passing ``configure_method_name``
and/or ``dependencies_method_name`` as args to ``new_object_graph()``.

.. code-block:: python

    >>> class NonStandardBindingSpec(pinject.BindingSpec):
    ...     def Configure(self, bind):
    ...         bind('forty_two', to_instance=42)
    ...
    >>> class SomeClass(object):
    ...     def __init__(self, forty_two):
    ...         self.forty_two = forty_two
    ...
    >>> obj_graph = pinject.new_object_graph(
    ...     binding_specs=[NonStandardBindingSpec()],
    ...     configure_method_name='Configure')
    >>> some_class = obj_graph.provide(SomeClass)
    >>> print some_class.forty_two
    42
    >>>

Customizing provider method names
---------------------------------

``new_object_graph()`` takes a ``get_arg_names_from_provider_fn_name`` arg.
This is the function that is used to identify provider methods on binding
specs.  This function takes in the name of a potential provider method (e.g.,
``provide_foo_bar``) and returns the arg names for which the provider method
is a provider, if any (e.g., ``['foo_bar']``).  Its default behavior is
described in the "provider methods" section above, but that default behavior
can be overridden.

For instance, suppose that you work for a certain large corporation whose
python style guide makes you name functions in ``CamelCase``, and so you need
to name the provider method for the arg name ``foo_bar`` more like
``ProvideFooBar`` than ``provide_foo_bar``.

.. code-block:: python

    >>> import re
    >>> def CustomGetArgNames(provider_fn_name):
    ...     if provider_fn_name.startswith('Provide'):
    ...         provided_camelcase = provider_fn_name[len('Provide'):]
    ...         return [re.sub('(?!^)([A-Z]+)', r'_\1', provided_camelcase).lower()]
    ...     else:
    ...         return []
    ...
    >>> print CustomGetArgNames('ProvideFooBar')
    ['foo_bar']
    >>> print CustomGetArgNames('ProvideFoo')
    ['foo']
    >>> class SomeClass(object):
    ...     def __init__(self, foo):
    ...         self.foo = foo
    ...
    >>> class SomeBindingSpec(pinject.BindingSpec):
    ...     def ProvideFoo(self):
    ...         return 'some-foo'
    ...
    >>> obj_graph = pinject.new_object_graph(
    ...     binding_specs=[SomeBindingSpec()],
    ...     get_arg_names_from_provider_fn_name=CustomGetArgNames)
    >>> some_class = obj_graph.provide(SomeClass)
    >>> print some_class.foo
    'some-foo'
    >>>

The function passed as the ``get_arg_names_from_provider_fn_name`` arg to
``new_object_graph()`` can return as many or as few arg names as it wants.  If
it returns an empty list, then that potential provider method is assumed not
actually to be a provider method.

Miscellaneous
=============

Pinject raises helpful exceptions whose messages include the file and line
number of errors.  So, Pinject by default will shorten the stack trace of
exceptions that it raises, so that you don't see the many levels of function
calls within the Pinject library.

In some situations, though, the complete stack trace is helpful, e.g., when
debugging Pinject, or when your code calls Pinject, which calls back into your
code, which calls back into Pinject.  In such cases, to disable exception
stack shortening, you can pass ``use_short_stack_traces=False`` to
``new_object_graph()``.

Gotchas
=======

Pinject has a few things to watch out for.

Thread safety
-------------

Pinject's default scope is ``SINGLETON``.  If you have a multi-threaded
program, it's likely that some or all of the things that Pinject provides from
singleton scope will be used in multiple threads.  So, it's important that you
ensure that such classes are thread-safe.

Similarly, it's important that your custom scope classes are thread-safe.
Even if the objects they provide are only used in a single thread, it may be
that the object graph (and therefore the scope itself) will be used
simultaneously in multiple threads.

Remember to make locks re-entrant on your custom scope classes, or otherwise
deal with one object in your custom scope trying to inject another object in
your custom scope.

That's it for gotchas, for now.

Condensed summary
=================

If you are already familiar with dependency injection libraries such as Guice,
this section gives you a condensed high level summary of Pinject and how it
might be similar to or different than other dependency injection libraries.
(If you don't understand it, no problem.  The rest of the documentation covers
everything listed here.)

* Pinject uses code and decorators to configure injection, not a separate config file.
* Bindings are keyed by arg name, (not class type, since Python is dynamically typed).
* Pinject automatically creates bindings to ``some_class`` arg names for ``SomeClass`` classes.
* You can ask Pinject only to create bindings from binding specs and classes whose ``__init__()`` is marked with ``@inject()``.
* A binding spec is a class that creates explicit bindings.
* A binding spec can bind arg names to classes or to instances.
* A binding spec can bind arg names ``foo`` to provider methods ``provide_foo()``.
* Binding specs can depend on (i.e., include) other binding specs.
* You can annotate args and bindings to distinguish among args/bindings for the same arg name.
* Pinject has two built-in scopes: "singleton" (always memoized; the default) and "prototype" (never memoized).
* You can define custom scopes, and you can configure which scopes are accessible from which other scopes.
* Pinject doesn't allow injecting ``None`` by default, but you can turn off that check.

Changelog
=========

v0.15: master

* Enable GitHub Actions
* CI/CD DevOps for publishing to PyPI automatically
* A version which the minor number is odd will be published as a `prerelease` and add `dev` to the patch version. (E.g. `0.15.0` will be published as `0.15.dev0` because the minor number `15` is odd)
* Remove Python version 3.3 & 3.4 from CI/CD `#50 <https://github.com/google/pinject/issues/50>`_

v0.12: 28 Nov, 2018

* Support Python 3
* Add two maintainers: @trein and @huan

v0.10.2:

* Fixed bug: allows binding specs containing only provider methods.

v0.10.1:

* Fixed bug: allows omitting custom named ``configure()`` binding spec method.

v0.10:

* Added default ``__eq__()`` to ``BindingSpec``, so that DAG binding spec dependencies can have equal but not identical dependencies.
* Allowed customizing ``configure()`` and ``dependencies()`` binding spec method names.
* Deprecated ``@injectable`` in favor of ``@inject``.
* Added partial injection.
* Added ``require`` arg to allow binding spec ``configure`` methods to declare but not define bindings.
* Sped up tests (and probably general functionality) by 10x.
* Documented more design decisions.
* Added ``@copy_args_to_internal_fields`` and ``@copy_args_to_public_fields``.
* Renamed ``InjectableDecoratorAppliedToNonInitError`` to ``DecoratorAppliedToNonInitError``.

v0.9:

* Added validation of python types of public args.
* Improved error messages for all Pinject-raised exceptions.
* Added ``use_short_stack_traces`` arg to ``new_object_graph()``.
* Allowed multiple ``@provides`` on single provider method.

v0.8:

* First released version.

Author
===========

Kurt Steinkraus `@kurt <https://github.com/kurt>`_

Maintainers
===========

* Guilherme Trein `@trein <https://github.com/trein>`_
* Huan LI `@huan <https://github.com/huan>`_

License
=======
Apache-2.0

Pinject and Google
==================

Though Google owns this project's copyright, this project is not an official
Google product.
