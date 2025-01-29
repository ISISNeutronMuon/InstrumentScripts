import os
import csv
import genie as g
import genie_advanced


class CaenThresholdSetter:
    def __init__(self,
                 threshold_scale_default: float,
                 absolute_threshold_default: int,
                 dsc_width_default: float) -> CaenThresholdSetter:
        # default value to scale all thresholds by
        self.threshold_scale_default = threshold_scale_default
        # default value for thresholds
        self.absolute_threshold_default = absolute_threshold_default
        # default value to write to discriminator output width register
        self.dsc_width_default = dsc_width_default
        self.enable_table_path = os.path.join("C:\\Instrument\\Settings\\config\\NDXCHRONUS\\Python\\tables",
                                              "enabled.csv")
        # Maximum number of crates in use by CAENs, increase if it is higher on any instrument
        self.max_crates = 3

    def find_cards(self) -> dict[int, int]:
        """
        A helper method that returns a dictionary of the number of cards on each connected crate
        :return: num_cards: The number of cards on each connected crate
        """
        num_cards = {}
        errors = []
        for crate in range(self.max_crates):
            try:
                cards = int(g.get_pv(g.prefix_pv_name(f"CAENV895_01:CR{crate}:CARDS")))
                num_cards[crate] = cards
            except Exception as e:
                errors.append(str(e))
        if len(num_cards) == 0:
            print("No crates found, raising the following errors:")
            raise Exception("\n".join(errors))
        return num_cards

    def set_thresholds(self,
                       threshold_scale: float = None,
                       dsc_width: float = None,
                       absolute_threshold: int = None,
                       re_enable: bool = False,
                       threshold_table: str = None) -> None:
        """
        Sets the thresholds and "enabled" status of every channel on every card in every crate. Can be supplied a
        single number or a file.

        :param threshold_scale: The value by which absolute threshold is scaled, if it is used. Defaults to the value
        provided upon init
        :param dsc_width: The discriminator widths to be set. Defaults to the value provided upon init
        :param absolute_threshold: The value to send uniformly to all channels, if no table is supplied. Defaults to the
        value provided upon init. NOTE: The  value sent to the CAEN will be rounded down to an integer AFTER multiplying
        this by threshold_scale.
        :param re_enable: Whether to ignore the table of which channels to enable and simply enable them all.
        :param threshold_table: The  path to a csv file containing the values to be set to each channel. If this
        argument is provided, the table will take priority over absolute thresholds
        :return: None
        """
        if threshold_scale is None:
            threshold_scale = self.threshold_scale_default
        if dsc_width is None:
            dsc_width = self.dsc_width_default
        if absolute_threshold is None:
            absolute_threshold = self.absolute_threshold_default

        num_cards = self.find_cards()
        num_crates = len(num_cards)

        voltage_threshold_table = {i: [] for i in range(num_crates)}
        enabled_cards_table = {i: [] for i in range(num_crates)}
        file_name = None  # Used later for updating a PV to track the current file

        if threshold_table:
            # A file was provided for the threshold table
            if os.path.isfile(threshold_table) and os.path.splitext(threshold_table)[1] == ".csv":
                # Check it actually exists nad is the correct format
                with open(threshold_table) as table_file:
                    table_reader = csv.reader(table_file)
                    crate_number = 0
                    for row in table_reader:
                        if not row:
                            # If there's an empty row, we interpret it as a delimiter between crates, so we first
                            # check that the current crate has the number of cards (and throw an error if not),
                            # then move on to the next crate
                            if len(voltage_threshold_table[crate_number]) != num_cards[crate_number]:
                                raise ValueError(f"Incorrect number of cards in crate, "
                                                 f"got {len(voltage_threshold_table[crate_number])}, "
                                                 f"expected {num_cards[crate_number]}")
                            crate_number += 1
                            continue
                        elif len(row) == 17:
                            # 16 channels + card number at the start, which we trim off as we append
                            voltage_threshold_table[crate_number].append(row[1:])
                        else:
                            raise ValueError(f"Incorrect number of channels in cards in {threshold_table}, "
                                             f"please provide 16 channels per card.")
                # Only after we're sure that the file is entirely valid do we set file_name to it
                file_name = threshold_table
            else:
                raise ValueError(
                    f"Incompatible file path {threshold_table}, please provide a valid path to a .csv file.")
        elif absolute_threshold:
            # Setting all channels to the same value
            for crate in voltage_threshold_table:
                voltage_threshold_table[crate] = [[absolute_threshold * threshold_scale] * 16] * num_cards[crate]
            # Make a new file with this value, if one doesn't already exist.
            file_name = f"constant_threshold_{int(absolute_threshold * threshold_scale)}V_" + "_".join(
                [str(cards) for _, cards in num_cards.items()]) + ".csv"
            file_path = os.path.join("C:\\Instrument\\Settings\\config\\NDXCHRONUS\\Python\\tables", file_name)
            if not os.path.isfile(file_path):
                with open(file_path, "w", newline='') as table_file:
                    table_writer = csv.writer(table_file)
                    for crate in voltage_threshold_table:
                        # for ease of reading, start each row with the card number
                        writen_crate = [[f"Card {i}:"] + voltage_threshold_table[crate][i]
                                        for i in range(num_cards[crate])]
                        table_writer.writerows(writen_crate)
                        # put a gap of 1 row between each crate
                        table_writer.writerow([])
        if re_enable:
            # if set, enable all channels
            for crate in enabled_cards_table:
                enabled_cards_table[crate] = [[1 * 16]] * num_cards[crate]
        else:
            with open(self.enable_table_path) as enable_table_file:
                enable_table_reader = csv.reader(enable_table_file)
                crate_number = 0
                for row in enable_table_reader:
                    if not row:
                        # If there's an empty row, we interpret it as a delimiter between crates, so we first check
                        # that the current crate has the number of cards (and throw an error if not), then move on to
                        # the next crate
                        if len(enabled_cards_table[crate_number]) != num_cards[crate_number]:
                            raise ValueError(f"Incorrect number of cards in crate {crate_number}, "
                                             f"got {len(enabled_cards_table[crate_number])}, "
                                             f"expected {num_cards[crate_number]}")
                        crate_number += 1
                        continue
                    elif len(row) == 17:
                        # 16 channels + card number at the start, which we trim off as we append
                        enabled_cards_table[crate_number].append(row[1:])
                    else:
                        raise ValueError("Incorrect number of channels in cards in enabled.csv, "
                                         "please provide 16 channels per card.")
        print("Setting thresholds and enabled status:")
        for crate in voltage_threshold_table:
            # first check that the IOC exists
            crate_pref = g.prefix_pv_name(f"CAENV895_01:CR{crate}")
            if not genie_advanced.pv_exists(f"{crate_pref}:CRATE"):
                raise ValueError(f"No IOC at {crate_pref}")
            # set the file being used
            g.set_pv(f"{crate_pref}:THRESHOLD_FILE", file_name)
            for card in range(num_cards[crate]):
                print(f"Setting crate {crate}, card {card}.")
                g.set_pv(f"{crate_pref}:C{card}:OUT:WIDTH:0_TO_7:SP", dsc_width)
                g.set_pv(f"{crate_pref}:C{card}:OUT:WIDTH:8_TO_15:SP", dsc_width)
                for channel in range(16):
                    # for each channel, set the threshold and enable based on the tables constructed
                    g.set_pv(f"{crate_pref}:C{card}:CH{channel}:THOLD:SP",
                             int(voltage_threshold_table[crate][card][channel]))
                    enabled = "YES" if enabled_cards_table[crate][card][channel] == "1" else "NO"
                    g.set_pv(f"{crate_pref}:C{card}:CH{channel}:ENABLE:SP", enabled)
        print("All cards set.")

    def tweak_thresholds(self, value: int) -> None:
        """
        Tweak all thresholds by a value
        :param value: The amount you wish to move every channel by
        :return: None
        """
        num_cards = self.find_cards()
        num_crates = len(num_cards)

        print(f"Tweaking all thresholds by {value}:")
        for crate in range(num_crates):
            crate_pref = g.prefix_pv_name(f"CAENV895_01:CR{crate}")
            for card in range(num_cards[crate]):
                print(f"Setting crate {crate}, card {card}.")
                for channel in range(16):
                    old_threshold = g.get_pv(f"{crate_pref}:C{card}:CH{channel}:THOLD:SP")
                    g.set_pv(f"{crate_pref}:C{card}:CH{channel}:THOLD:SP", int(old_threshold + value))
        print("All cards set.")
