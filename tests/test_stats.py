"""Tests for statistical functions."""

from crystallize.stats import permutation_test, bootstrap_ci, effect_size, check_hypothesis


class TestPermutationTest:
    """Tests for permutation_test()."""

    def test_clear_difference(self):
        """Permutation test detects clear differences."""
        a = [10, 11, 12, 10, 11]
        b = [1, 2, 1, 2, 1]

        p = permutation_test(a, b, ">", n_permutations=1000, seed=42)
        assert p < 0.05  # Should be significant

    def test_no_difference(self):
        """Permutation test doesn't detect non-existent differences."""
        a = [5, 5, 5, 5, 5]
        b = [5, 5, 5, 5, 5]

        p = permutation_test(a, b, ">", n_permutations=1000, seed=42)
        assert p > 0.1  # Should not be significant

    def test_opposite_direction(self):
        """Permutation test respects operator direction."""
        a = [1, 2, 1, 2, 1]
        b = [10, 11, 12, 10, 11]

        p_greater = permutation_test(a, b, ">", n_permutations=1000, seed=42)
        p_less = permutation_test(a, b, "<", n_permutations=1000, seed=42)

        assert p_greater > 0.5  # a > b should NOT be supported
        assert p_less < 0.05  # a < b SHOULD be supported

    def test_empty_samples(self):
        """Permutation test handles empty samples."""
        p = permutation_test([], [1, 2, 3], ">")
        assert p != p  # NaN

    def test_reproducible_with_seed(self):
        """Permutation test is reproducible with same seed."""
        a = [1, 2, 3, 4, 5]
        b = [6, 7, 8, 9, 10]

        p1 = permutation_test(a, b, ">", n_permutations=500, seed=42)
        p2 = permutation_test(a, b, ">", n_permutations=500, seed=42)

        assert p1 == p2


class TestBootstrapCI:
    """Tests for bootstrap_ci()."""

    def test_ci_contains_effect(self):
        """Bootstrap CI contains the true effect."""
        a = [10, 11, 12, 10, 11]
        b = [5, 6, 5, 6, 5]

        lower, upper = bootstrap_ci(a, b, n_resamples=1000, seed=42)
        true_effect = sum(a) / len(a) - sum(b) / len(b)

        assert lower < true_effect < upper

    def test_ci_width_shrinks_with_more_data(self):
        """CI width decreases with more data points."""
        import random

        random.seed(42)
        small = [10 + random.random() for _ in range(5)]
        large = [10 + random.random() for _ in range(50)]
        baseline = [5 + random.random() for _ in range(50)]

        _, upper_small = bootstrap_ci(small, baseline[:5], seed=42)
        lower_small, _ = bootstrap_ci(small, baseline[:5], seed=42)
        width_small = upper_small - lower_small

        lower_large, upper_large = bootstrap_ci(large, baseline, seed=42)
        width_large = upper_large - lower_large

        assert width_large < width_small

    def test_empty_samples(self):
        """Bootstrap CI handles empty samples."""
        lower, upper = bootstrap_ci([], [1, 2, 3])
        assert lower != lower  # NaN


class TestEffectSize:
    """Tests for effect_size()."""

    def test_positive_effect(self):
        """Effect size is positive when a > b."""
        a = [10, 11, 12]
        b = [1, 2, 3]

        eff = effect_size(a, b)
        assert eff > 0

    def test_negative_effect(self):
        """Effect size is negative when a < b."""
        a = [1, 2, 3]
        b = [10, 11, 12]

        eff = effect_size(a, b)
        assert eff < 0

    def test_zero_effect(self):
        """Effect size is zero when a == b."""
        a = [5, 5, 5]
        b = [5, 5, 5]

        eff = effect_size(a, b)
        assert eff == 0


class TestCheckHypothesis:
    """Tests for check_hypothesis()."""

    def test_supported_greater_than(self):
        """check_hypothesis() supports a > b when true."""
        a = [10, 11, 12, 10, 11, 12, 10, 11, 12, 10]
        b = [1, 2, 1, 2, 1, 2, 1, 2, 1, 2]

        supported, eff, p, ci = check_hypothesis(a, b, ">", seed=42)

        assert supported is True
        assert eff > 0
        assert p < 0.05
        assert ci[0] > 0  # CI should be positive

    def test_not_supported_when_false(self):
        """check_hypothesis() doesn't support false hypothesis."""
        a = [5, 5, 5, 5, 5]
        b = [5, 5, 5, 5, 5]

        supported, eff, p, ci = check_hypothesis(a, b, ">", seed=42)

        assert supported is False

    def test_less_than_operator(self):
        """check_hypothesis() works with < operator."""
        a = [1, 2, 1, 2, 1, 2, 1, 2, 1, 2]
        b = [10, 11, 12, 10, 11, 12, 10, 11, 12, 10]

        supported, eff, p, ci = check_hypothesis(a, b, "<", seed=42)

        assert supported is True
        assert eff < 0
        assert p < 0.05
