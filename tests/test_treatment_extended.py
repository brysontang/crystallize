"""Extended tests for Treatment class."""

import pytest

from crystallize.experiments.treatment import Treatment, _MappingApplier
from crystallize.utils.context import FrozenContext
from crystallize.utils.exceptions import ContextMutationError


class TestTreatmentApplyMap:
    """Tests for Treatment.apply_map property."""

    def test_apply_map_with_mapping(self):
        treatment = Treatment("test", {"lr": 0.01, "batch_size": 32})
        assert treatment.apply_map == {"lr": 0.01, "batch_size": 32}

    def test_apply_map_with_callable_returns_empty(self):
        def custom_apply(ctx):
            ctx.add("custom", "value")

        treatment = Treatment("test", custom_apply)
        assert treatment.apply_map == {}

    def test_apply_map_with_empty_mapping(self):
        treatment = Treatment("empty", {})
        assert treatment.apply_map == {}

    def test_apply_map_with_complex_values(self):
        mapping = {
            "list": [1, 2, 3],
            "dict": {"nested": True},
            "tuple": (1, 2),
        }
        treatment = Treatment("complex", mapping)
        assert treatment.apply_map == mapping


class TestTreatmentApply:
    """Tests for Treatment.apply() method."""

    def test_apply_with_mapping_adds_keys(self):
        treatment = Treatment("test", {"x": 1, "y": 2})
        ctx = FrozenContext({})
        treatment.apply(ctx)

        assert ctx["x"] == 1
        assert ctx["y"] == 2

    def test_apply_with_callable(self):
        def custom_apply(ctx):
            ctx.add("computed", 10 * 2)

        treatment = Treatment("custom", custom_apply)
        ctx = FrozenContext({})
        treatment.apply(ctx)

        assert ctx["computed"] == 20

    def test_apply_raises_on_existing_key(self):
        treatment = Treatment("conflict", {"existing": "new_value"})
        ctx = FrozenContext({"existing": "original"})

        with pytest.raises(ContextMutationError):
            treatment.apply(ctx)

    def test_apply_with_none_values(self):
        treatment = Treatment("nullable", {"key": None})
        ctx = FrozenContext({})
        treatment.apply(ctx)

        assert ctx["key"] is None


class TestMappingApplier:
    """Tests for _MappingApplier internal class."""

    def test_mapping_applier_is_callable(self):
        applier = _MappingApplier({"a": 1})
        assert callable(applier)

    def test_mapping_applier_adds_items(self):
        applier = _MappingApplier({"x": 10, "y": 20})
        ctx = FrozenContext({})
        applier(ctx)

        assert ctx["x"] == 10
        assert ctx["y"] == 20

    def test_mapping_applier_stores_items(self):
        mapping = {"key": "value"}
        applier = _MappingApplier(mapping)
        assert applier.items == mapping

    def test_mapping_applier_is_picklable(self):
        import pickle

        applier = _MappingApplier({"data": [1, 2, 3]})
        pickled = pickle.dumps(applier)
        restored = pickle.loads(pickled)

        assert restored.items == applier.items


class TestTreatmentPicklability:
    """Tests for Treatment pickling for multiprocessing."""

    def test_treatment_with_mapping_is_picklable(self):
        import pickle

        treatment = Treatment("pickled", {"param": 42})
        pickled = pickle.dumps(treatment)
        restored = pickle.loads(pickled)

        assert restored.name == "pickled"
        assert restored.apply_map == {"param": 42}

    def test_treatment_with_mapping_preserves_behavior(self):
        import pickle

        treatment = Treatment("test", {"x": 1})
        restored = pickle.loads(pickle.dumps(treatment))

        ctx = FrozenContext({})
        restored.apply(ctx)
        assert ctx["x"] == 1


class TestTreatmentEdgeCases:
    """Edge cases for Treatment class."""

    def test_treatment_name_with_special_chars(self):
        treatment = Treatment("test-name_v2.0", {"key": 1})
        assert treatment.name == "test-name_v2.0"

    def test_treatment_with_empty_name(self):
        treatment = Treatment("", {"key": 1})
        assert treatment.name == ""

    def test_treatment_callable_with_no_side_effects(self):
        def noop(ctx):
            pass

        treatment = Treatment("noop", noop)
        ctx = FrozenContext({"original": True})
        treatment.apply(ctx)

        # Original data still there, nothing added
        assert ctx["original"] is True
        assert ctx.as_dict() == {"original": True}

    def test_treatment_callable_can_read_context(self):
        def conditional_apply(ctx):
            if ctx.get("mode") == "test":
                ctx.add("test_param", 100)
            else:
                ctx.add("prod_param", 200)

        treatment = Treatment("conditional", conditional_apply)

        # Test mode
        ctx1 = FrozenContext({"mode": "test"})
        treatment.apply(ctx1)
        assert ctx1["test_param"] == 100

        # Prod mode
        ctx2 = FrozenContext({"mode": "prod"})
        treatment.apply(ctx2)
        assert ctx2["prod_param"] == 200
