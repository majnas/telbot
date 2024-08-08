from fpdf import FPDF

def create_pdf_with_text(file_path, text):
    header, data = get_data_from_prettytable(text)
    export_to_pdf(file_path, header, data)

def create_txt(file_path, text):
    with open(file_path, 'w') as f:
        f.write(text)

# https://stackoverflow.com/questions/56018608/table-from-prettytable-to-pdf
def get_data_from_prettytable(x):
    """
    Get a list of list from pretty_data table
    Arguments:
        :param data: data table to process
        :type data: PrettyTable
    """

    def remove_space(liste):
        """
        Remove space for each word in a list
        Arguments:
            :param liste: list of strings
        """   
        list_without_space = []
        for mot in liste:                                       # For each word in list
            word_without_space = mot.replace(' ', '')           # word without space
            list_without_space.append(word_without_space)       # list of word without space
        return list_without_space

    # Get each row of the table
    string_x = str(x).split('\n')                               # Get a list of row
    header = string_x[1].split('|')[1: -1]                      # Columns names
    rows = string_x[3:len(string_x) - 1]                        # List of rows

    list_word_per_row = []
    for row in rows:                                            # For each word in a row
        row_resize = row.split('|')[1:-1]                       # Remove first and last arguments
        list_word_per_row.append(remove_space(row_resize))      # Remove spaces

    return header, list_word_per_row


def export_to_pdf(file_path, header, data):
    """
    Create a a table in PDF file from a list of row
        :param header: columns name
        :param data: List of row (a row = a list of cells)
        :param spacing=1: 
    """
    pdf = FPDF(orientation='landscape')                                # New  pdf object

    pdf.set_font("Arial", size=6)              # Font style
    epw = pdf.w - 2*pdf.l_margin                # Witdh of document
    col_width = pdf.w / 15                     # Column width in table
    row_height = pdf.font_size * 3            # Row height in table
    spacing = 0.8                               # Space in each cell

    pdf.add_page()                              # add new page

    pdf.cell(epw, 0.0, 'My title', align='C')   # create title cell
    pdf.ln(row_height*spacing)                  # Define title line style

    # Add header
    for item in header:                         # for each column
        pdf.cell(col_width, row_height*spacing, # Add a new cell
                 txt=item, border=1)
    pdf.ln(row_height*spacing)                  # New line after header

    for row in data:                            # For each row of the table
        for item in row:                        # For each cell in row
            pdf.cell(col_width, row_height*spacing, # Add cell
                    txt=item, border=1)
        pdf.ln(row_height*spacing)              # Add line at the end of row

    pdf.output(file_path)                       # Create pdf file 
    pdf.close()                                 # Close file