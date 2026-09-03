from __future__ import annotations

from car_damage.dataset import check_dataset


def test_current_dataset_passes_full_validation() -> None:
    report = check_dataset(verify_images=True)
    assert report.ok
    train, val = report.splits
    assert (train.images, train.labels, train.objects, train.empty_labels) == (4560, 4560, 7731, 5)
    assert (val.images, val.labels, val.objects, val.empty_labels) == (1140, 1140, 2043, 1)
    assert train.class_counts == {0: 4843, 1: 764, 2: 2124}
    assert val.class_counts == {0: 1355, 1: 206, 2: 482}
    assert len(train.warnings) == 3
    assert not val.warnings
