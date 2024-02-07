"""
Sample classes for reflectometry
"""


class SampleGenerator:
    """
    Sample generator to create samples based on some defaults
    """

    def __init__(self, translation, height2_offset, phi_offset, psi_offset, height_offset, resolution, footprint,
                 sample_length, valve, hgaps, title="", subtitle=""):
        """
        Initialiser.
        Args:
            translation: The translation for the sample
            height_offset: Height between the sample and center of rotation; If no height stage 2 then this needs to
                have the offset to the beam added
            height2_offset: Height of the second stage with no mirror relative to the beam for this sample
            phi_offset: offset from 0 for the sample in the phi direction (along the beam)
            psi_offset: offset from 0 for the sample in the psi direction (perpendicular to the beam)
            resolution: resolution for this sample
            footprint: footprint of beam on sample
            title: main title for the sample; defaults to blank
            subtitle: subtitle for the sample; defaults to blank
        """
        self.subtitle = subtitle
        self.title = title
        self.footprint = float(footprint)
        self.resolution = float(resolution)
        self.height_offset = float(height_offset)
        self.psi_offset = float(psi_offset)
        self.phi_offset = float(phi_offset)
        self.translation = float(translation)
        self.height2_offset = float(height2_offset)
        self.sample_length = float(sample_length)
        self.valve = int(valve)
        self.hgaps = dict(hgaps)

    def new_sample(self, title=None, subtitle=None, translation=None, height2_offset=None, phi_offset=None,
                   psi_offset=None, height_offset=None, resolution=None, footprint=None,
                   sample_length=None, valve=None, hgaps=None):
        """
        Create a new sample with given values; if no value defined use defaults
        Args:
            translation: The translation for the sample
            height_offset: Height between the sample and center of rotation; If no height stage 2 then this needs to
                have the offset to the beam added
            height2_offset: Height of the second stage with no mirror relative to the beam for this sample
            phi_offset: offset from 0 for the sample in the phi direction (along the beam)
            psi_offset: offset from 0 for the sample in the psi direction (perpendicular to the beam)
            height_offset: Offset for height of main stage
            resolution: resolution for this sample
            footprint: footprint of beam on sample
            title: main title for the sample; defaults to blank
            subtitle: subtitle for the sample; defaults to blank
        """
        if title is None:
            title = self.title
        if subtitle is None:
            subtitle = self.subtitle
        if translation is None:
            translation = self.translation
        if height2_offset is None:
            height2_offset = self.height2_offset
        if phi_offset is None:
            phi_offset = self.phi_offset
        if psi_offset is None:
            psi_offset = self.psi_offset
        if height_offset is None:
            height_offset = self.height_offset
        if resolution is None:
            resolution = self.resolution
        if footprint is None:
            footprint = self.footprint
        if sample_length is None:
            sample_length = self.sample_length
        if valve is None:
            valve = self.valve
        if hgaps is None:
            hgaps = self.hgaps

        return Sample(title, subtitle, translation, height2_offset, phi_offset, psi_offset,
                      height_offset, resolution, footprint, sample_length, valve, hgaps)

    def __repr__(self):
        return "Sample generator: {}".format(self.__dict__)


class Sample:
    """
    A sample definition

    """

    def __init__(self, title, subtitle, translation, height2_offset, phi_offset, psi_offset, height_offset,
                 resolution, footprint, sample_length, valve, hgaps):
        """
        Initialiser.
        Args:
            translation: The translation for the sample
            height_offset: Height between the sample and center of rotation; If no height stage 2 then this needs to
                have the offset to the beam added
            height2_offset: Height of the second stage with no mirror relative to the beam for this sample
            phi_offset: offset from 0 for the sample in the phi direction (along the beam)
            psi_offset: offset from 0 for the sample in the psi direction (perpendicular to the beam)
            resolution: resolution for this sample
            footprint: footprint of beam on sample
            title: main title for the sample; defaults to blank
            subtitle: subtitle for the sample; defaults to blank
        """
        self.subtitle = subtitle
        self.title = title
        self.footprint = footprint
        self.resolution = resolution
        self.height_offset = height_offset
        self.psi_offset = psi_offset
        self.phi_offset = phi_offset
        self.translation = translation
        self.height2_offset = height2_offset
        self.sample_length = float(sample_length)
        self.valve = int(valve)
        self.hgaps = dict(hgaps)

    def __repr__(self):
        return "Sample: {}".format(self.__dict__)
