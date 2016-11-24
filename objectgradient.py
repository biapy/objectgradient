# coding: utf-8
#!/usr/bin/env python
"""
#  objectgradient.py
#
#  Copyright 2011
#
#   Pierre-Yves Landuré
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Idc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
"""


# This is only needed if the extension is not called by inkscape (?)
import sys
sys.path.append('/usr/share/inkscape/extensions')

### Inkscape imports
# Import Inkscape inkex module with the predefined Effect base class.
import inkex
# The simplestyle module provides functions for style parsing.
from simplestyle import parseStyle, formatStyle
from simpletransform import computeBBox
### End of Inkscape imports.

# Import system necessary libraries.
import os
import csv

# Import subprocess Popen,
# to call on inkscape to mesure Text element size.
try:
    from subprocess import Popen, PIPE
    BSUBPROCESS = True
except ImportError:
    BSUBPROCESS = False



class ObjectGradient(inkex.Effect):
    """
    Inkscape Color extension for gradient generation.
    This extention apply a gradient of color fill to selected objects from first selected
    to last selected.
    """

    def __init__(self):
        """
        Effect Constructor.
        Describe the python script options.
        """
        # Call the base class constructor.
        inkex.Effect.__init__(self)

        self.OptionParser.add_option("-s", "--start-color", action="store",
                                     type="string", dest="start_color", default='0',
                                     help="Gradient starting color")

        self.OptionParser.add_option("-e", "--end-color", action="store",
                                     type="string", dest="end_color", default='0',
                                     help="Gradient starting color")

        self.OptionParser.add_option("", "--gradient-orientation", action="store",
                                     type="string", dest="gradient_orientation", default='left-to-right',
                                     help="Gradient orientation (used to sort selection).")

        self.OptionParser.add_option("", "--stroke-only", action="store",
                                     type="inkbool", dest="stroke_only", default='False',
                                     help="True if gradient applied to stroke.")



    def get_dimensions(self, nodes_ids_list):
        """
        Get dimensions of nodes with given ids.
        """
        if len(nodes_ids_list) > 0:
            svg_file = self.args[-1]

            #get all bounding boxes in file by calling inkscape again
            #with the --query-all command line option
            #it returns a comma seperated list structured id,x,y,w,h
            if BSUBPROCESS:
                inkscape_pipe = Popen('inkscape --query-all "%s"' % (svg_file),
                                      shell=True, stdout=PIPE, stderr=PIPE)
                err = inkscape_pipe.stderr
                inkscape_output = inkscape_pipe.communicate()[0]
                try:
                    reader = csv.CSVParser().parse_string(inkscape_output)
                    #there was a module cvs.py in earlier inkscape that behaved differently
                except:
                    reader = csv.reader(inkscape_output.split(os.linesep))
                err.close()
            else:
                _, inkscape_output, err = os.popen3('inkscape --query-all "%s"' % (svg_file))
                reader = csv.reader(inkscape_output)
                err.close()

            #build a dictionary with id as the key
            dimensions = dict()
            for line in reader:
                if (len(line) > 0) and (line[0] in nodes_ids_list):
                    dimensions[line[0]] = map(float, line[1:])

            if not BSUBPROCESS: #close file if opened using os.popen3
                inkscape_output.close

        return dimensions


    def get_node_style(self, node):
        """
        Sugar coated way to get style dict from a node

        Argument:
        node -- SVG element as XML node.

        Return:
        node parsed style values as dictionnary.
        """
        if 'style' in node.attrib:
            return parseStyle(node.attrib['style'])



    def set_node_style(self, node, style):
        """
        Sugar coated way to set the style dict, for node

        Argument:
        node -- SVG element as XML node.
        style -- style dictionnary.
        """
        node.attrib['style'] = formatStyle(style)



    def unsigned_long(self, signed_long_string):
        """
        Convert a signed long represented as string to unsigned long.
        @see: http://www.hoboes.com/Mimsy/hacks/parsing-and-setting-colors-inkscape-extensions/

        Arguments:
        signed_long_string -- A signed long represented as string (string).

        Return:
        A unsigned long value.
        """
        unsigned_long = long(signed_long_string)
        if unsigned_long < 0:
            unsigned_long = unsigned_long & 0xFFFFFFFF
        return unsigned_long



    def get_color_hexa_string(self, long_color):
        """
        Convert a color from long representation to string representation.
        @see: http://www.hoboes.com/Mimsy/hacks/parsing-and-setting-colors-inkscape-extensions/

        Long color is obainted by this formula:
        long_color = A*256^0 + B*256^1 + G*256^2 + R*256^3
        where:
            A is alpha channel, B is Blue channel, G is green channel, R is red channel.
            All channels are expressed by int values from 0 to 255.

        Argument:
        long_color: color as long (long).

        Return:
        The color as a hexadecimal string value.
        """
        unsigned_long = self.unsigned_long(long_color)
        hex_color = hex(unsigned_long)[2:-3]
        hex_color = hex_color.rjust(6, '0')
        return '#' + hex_color.upper()



    def get_color_dictionnary(self, long_color):
        """
        Convert a color from long version to a dictionnary.

        Arguments:
        long_color: color as long (long).

        Return:
        The color as a dictionnary of 0 to 255 in values:
            { 'r': int(0-255), 'g': int(0-255), 'b': int(0-255), a': float(0-1) }.
        """
        color_dictionnary = {'r' : 0, 'g' : 0, 'b' : 0, 'a' : 0}

        unsigned_long = self.unsigned_long(long_color)
        # Convert to hexa and remove "0x" from string head and "L" from string tail.
        hex_color = hex(unsigned_long)[2:-1]
        hex_color = hex_color.rjust(8, '0')

        color_dictionnary['r'] = int(hex_color[0:2], 16)
        color_dictionnary['g'] = int(hex_color[2:4], 16)
        color_dictionnary['b'] = int(hex_color[4:6], 16)
        color_dictionnary['a'] = float(int(hex_color[6:8], 16)) / 255

        return color_dictionnary



    def color_dictionnary_to_alpha(self, color_dictionnary):
        """
        Return the color dictionnary alpha component.

        Arguments:
        color_dictionnary -- A color as dictionnary.

        Return:
        Alpha component as float(0-1).
        """
        return color_dictionnary['a']



    def color_dictionnary_to_hex(self, color_dictionnary):
        """
        Return the color dictionnary color component as hexa string.

        Arguments:
        color_dictionnary -- A color as dictionnary.

        Return:
        Color as web string (#xxxxxx)
        """
        return '#%s%s%s' % (
            hex(color_dictionnary['r'])[2:4].rjust(2, '0'),
            hex(color_dictionnary['g'])[2:4].rjust(2, '0'),
            hex(color_dictionnary['b'])[2:4].rjust(2, '0')
        )



    def get_color_gradients(self, start_color_dictionnary, end_color_dictionnary, steps):
        """
        Generated gradients steps from start color to end color.

        Arguments:
        start_color_dictionnary -- A color represented by a dictionnary.
        end_color_dictionnary -- A color represented by a dictionnary.
        steps -- Number of gradient steps between starting color and ending color (included).

        Return:
        A list of gradient colors as dictionnaries.
        """
        gradient_steps = [start_color_dictionnary]

        if steps > 2:
            # Compute the gradient steps.
            gradient_step_dictionnary = {
                'r' : (end_color_dictionnary['r'] - start_color_dictionnary['r']) / (steps - 1),
                'g' : (end_color_dictionnary['g'] - start_color_dictionnary['g']) / (steps - 1),
                'b' : (end_color_dictionnary['b'] - start_color_dictionnary['b']) / (steps - 1),
                'a' : (end_color_dictionnary['a'] - start_color_dictionnary['a']) / (steps - 1)
            }

            # Generated transient gradient colors.
            for step_index in range(1, steps -1):
                current_gradient_dictionnary = {
                    'r' : int(start_color_dictionnary['r']
                              + (gradient_step_dictionnary['r'] * step_index)),
                    'g' : int(start_color_dictionnary['g']
                              + (gradient_step_dictionnary['g'] * step_index)),
                    'b' : int(start_color_dictionnary['b']
                              + (gradient_step_dictionnary['b'] * step_index)),
                    'a' : start_color_dictionnary['a']
                          + (gradient_step_dictionnary['a'] * step_index)
                }

                # Check computed gradient color boundaries.
                for color in ('r', 'g', 'b'):
                    if current_gradient_dictionnary[color] > 255:
                        current_gradient_dictionnary[color] = 255
                    if current_gradient_dictionnary[color] < 0:
                        current_gradient_dictionnary[color] = 0

                if current_gradient_dictionnary['a'] > 1:
                    current_gradient_dictionnary['a'] = 1

                if current_gradient_dictionnary['a'] < 0:
                    current_gradient_dictionnary['a'] = 0

                gradient_steps.append(current_gradient_dictionnary)

        # Add end color to gradient.
        gradient_steps.append(end_color_dictionnary)

        return gradient_steps



    def set_node_stroke_color(self, node, color_dictionnary):
        """
        Set a node stroke color from a color dictionnary.

        Argument:
        node -- SVG element as XML node.
        color_dictionnary -- stroke color as dictionnary.

        Return:
        True if the style change has been applied.
        """
        style_changed = False

        style = self.get_node_style(node)
        if style:
            style['stroke'] = self.color_dictionnary_to_hex(color_dictionnary)
            style['stroke-opacity'] = self.color_dictionnary_to_alpha(color_dictionnary)
            self.set_node_style(node, style)
            style_changed = True
        return style_changed



    def set_node_fill_color(self, node, color_dictionnary):
        """
        Set a node fill color from a color dictionnary.

        Argument:
        node -- SVG element as XML node.
        color_dictionnary -- Fill color as dictionnary.

        Return:
        True if the style change has been applied.
        """
        style_changed = False

        style = self.get_node_style(node)
        if style:
            style['fill'] = self.color_dictionnary_to_hex(color_dictionnary)
            style['fill-opacity'] = self.color_dictionnary_to_alpha(color_dictionnary)
            self.set_node_style(node, style)
            style_changed = True
        return style_changed



    def effect(self):
        """
        Effect behaviour.
        Overrides base class' method and inserts a drowsing looking chart into SVG document.
        """

        # Get access to main SVG document element and get its dimensions.
        #svg = self.document.getroot()

        start_color_dictionnary = self.get_color_dictionnary(self.options.start_color)
        end_color_dictionnary = self.get_color_dictionnary(self.options.end_color)

        steps = len(self.selected)

        selection_dimensions = self.get_dimensions(self.options.ids)

        if self.options.gradient_orientation == 'top-to-bottom':
            sorted_selection_dimensions = sorted(selection_dimensions.items(),
                                                 key=lambda node_infos: node_infos[1][1])
        elif self.options.gradient_orientation == 'bottom-to-top':
            sorted_selection_dimensions = sorted(selection_dimensions.items(),
                                                 key=lambda node_infos: node_infos[1][1] + node_infos[1][3],
                                                 reverse=True)
        elif self.options.gradient_orientation == 'right-to-left':
            sorted_selection_dimensions = sorted(selection_dimensions.items(),
                                                 key=lambda node_infos: node_infos[1][0] + node_infos[1][2],
                                                 reverse=True)
        else:
            # Sort dimensions by X first:
            sorted_selection_dimensions = sorted(selection_dimensions.items(),
                                                 key=lambda node_infos: node_infos[1][0])

        # If more than one object selected.
        if steps > 1:
            color_gradients = self.get_color_gradients(start_color_dictionnary,
                                                       end_color_dictionnary,
                                                       steps)

            gradient_index = 0
            for node_id, node_infos in sorted_selection_dimensions:
                # Change node fill color.
                node = self.selected[node_id]
                if self.options.stroke_only:
                    self.set_node_stroke_color(node, color_gradients[gradient_index])
                else:
                    self.set_node_fill_color(node, color_gradients[gradient_index])
                gradient_index += 1


# Create effect instadce and apply it.
effect = ObjectGradient()
effect.affect()
