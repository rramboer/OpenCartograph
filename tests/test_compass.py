"""Tests for opencartograph.rendering.compass."""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from opencartograph.rendering.compass import draw_north_badge


class TestDrawNorthBadge:
    def _make_axes(self):
        fig, ax = plt.subplots()
        ax.set_xlim(0, 1000)
        ax.set_ylim(0, 1000)
        return fig, ax

    def test_adds_patches_and_text(self):
        fig, ax = self._make_axes()
        n_patches_before = len(ax.patches)
        n_texts_before = len(ax.texts)
        draw_north_badge(ax, orientation_offset=45, text_color="#000000")
        assert len(ax.patches) == n_patches_before + 1  # arrow
        assert len(ax.texts) == n_texts_before + 1  # "N" label
        plt.close(fig)

    def test_label_is_n(self):
        fig, ax = self._make_axes()
        draw_north_badge(ax, orientation_offset=0, text_color="#FF0000")
        assert ax.texts[-1].get_text() == "N"
        plt.close(fig)

    def test_uses_theme_color(self):
        fig, ax = self._make_axes()
        draw_north_badge(ax, orientation_offset=0, text_color="#FF0000")
        assert ax.texts[-1].get_color() == "#FF0000"
        plt.close(fig)

    def test_zero_rotation_arrow_points_up(self):
        fig, ax = self._make_axes()
        draw_north_badge(ax, orientation_offset=0, text_color="#000000")
        arrow = ax.patches[-1]
        # Arrow tip should be above arrow base (higher y)
        posA = arrow._posA_posB[0]
        posB = arrow._posA_posB[1]
        assert posB[1] > posA[1]  # tip y > base y
        plt.close(fig)

    def test_different_offsets_produce_different_positions(self):
        fig1, ax1 = self._make_axes()
        draw_north_badge(ax1, orientation_offset=0, text_color="#000000")
        pos0 = ax1.texts[-1].get_position()
        plt.close(fig1)

        fig2, ax2 = self._make_axes()
        draw_north_badge(ax2, orientation_offset=90, text_color="#000000")
        pos90 = ax2.texts[-1].get_position()
        plt.close(fig2)

        assert pos0 != pos90
