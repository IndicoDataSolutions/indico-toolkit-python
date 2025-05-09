from indico_toolkit.snapshots import Snapshot

PATH_TO_SNAPSHOT = "./snapshot_1.csv"
PATH_TO_SNAPSHOT_2 = "./snapshot_2.csv"
OUTPUT_PATH = "./merged_snapshot_output.csv"

"""
EXAMPLE 1: Merge the labels from two downloaded teach task snapshots on the same files.
Example usage: if you labeled different fields for the same documents in separate tasks.
"""
main_snap = Snapshot(PATH_TO_SNAPSHOT)
snap_to_merge = Snapshot(PATH_TO_SNAPSHOT_2)
main_snap.standardize_column_names()
snap_to_merge.standardize_column_names()
main_snap.merge_by_file_name(snap_to_merge, ensure_identical_text=True)
# see what text was captured for any label
print(main_snap.get_all_labeled_text("Company Name"))
main_snap.to_csv(OUTPUT_PATH, only_keep_key_columns=True)

"""
EXAMPLE 2: Combine two identically labeled snapshots together
Example usage: if you labeled different documents with the same labels in separate tasks
"""
main_snap = Snapshot(PATH_TO_SNAPSHOT)
print(main_snap.number_of_samples)
snap_to_append = Snapshot(PATH_TO_SNAPSHOT_2)
main_snap.standardize_column_names()
snap_to_append.standardize_column_names()
main_snap.append(snap_to_append)
# will now include all of the samples from snap_to_append as well
print(main_snap.number_of_samples)
main_snap.to_csv(OUTPUT_PATH)
