import flet as ft

class PragatiApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "PRAGATI - Digital Governance Platform"
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.padding = 20
        
        # Safe universal FilePicker setup
        self.citizen_file_picker = ft.FilePicker()
        self.page.overlay.append(self.citizen_file_picker)
        
        self.build_login_screen()

    def build_login_screen(self):
        self.page.clean()
        
        title = ft.Text("PRAGATI PLATFORM", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)
        subtitle = ft.Text("Public Responsibility & Governance Accountability Tech Initiative", size=14, color=ft.Colors.GREY_600)
        
        # Replaced with native content mappings to bypass keyword restrictions
        citizen_btn = ft.ElevatedButton(
            content=ft.Text("Citizen Portal Login", size=16),
            width=300, 
            height=50,
            on_click=lambda _: self.build_citizen_dashboard()
        )
        
        gov_btn = ft.ElevatedButton(
            content=ft.Text("Government Official Login", size=16),
            width=300, 
            height=50,
            on_click=lambda _: self.build_gov_dashboard()
        )
        
        self.page.add(
            ft.Column(
                [
                    ft.Container(height=50),
                    title,
                    subtitle,
                    ft.Container(height=40),
                    citizen_btn,
                    ft.Container(height=10),
                    gov_btn
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
        self.page.update()

    def build_citizen_dashboard(self):
        self.page.clean()
        
        finance_row = ft.Row(
            [
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Total Taxes Collected", size=16, color=ft.Colors.WHITE),
                            ft.Text("₹ 4,50,000 Cr", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ]),
                        padding=20, width=250, bgcolor=ft.Colors.GREEN_700, border_radius=10
                    )
                ),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Total Funds Expended", size=16, color=ft.Colors.WHITE),
                            ft.Text("₹ 2,10,000 Cr", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ]),
                        padding=20, width=250, bgcolor=ft.Colors.BLUE_700, border_radius=10
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        complaint_input = ft.TextField(label="Describe your infrastructure issue (e.g. Bad Roads, Water)", multiline=True, min_lines=3, width=500)
        pincode_input = ft.TextField(label="Enter Area PIN Code", width=200)
        
        upload_btn = ft.ElevatedButton(content=ft.Text("Upload Image Proof"), on_click=lambda _: self.citizen_file_picker.pick_files())
        submit_btn = ft.ElevatedButton(content=ft.Text("Submit Complaint to National Ledger"), width=500, height=45)
        
        back_btn = ft.TextButton(content=ft.Text("Back to Selection"), on_click=lambda _: self.build_login_screen())
        
        self.page.add(
            ft.Column(
                [
                    ft.Row([back_btn, ft.Text("Citizen Accountability Dashboard", size=22, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=600),
                    ft.Divider(),
                    finance_row,
                    ft.Container(height=20),
                    ft.Text("Raise a New Local Infrastructure Complaint", size=16, weight=ft.FontWeight.BOLD),
                    complaint_input,
                    ft.Row([pincode_input, upload_btn], alignment=ft.MainAxisAlignment.CENTER, width=500),
                    ft.Container(height=10),
                    submit_btn
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
        self.page.update()

    def build_gov_dashboard(self):
        self.page.clean()
        
        finance_row = ft.Row(
            [
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Total Budget Allocated", size=16, color=ft.Colors.WHITE),
                            ft.Text("₹ 4,50,000 Cr", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ]),
                        padding=20, width=250, bgcolor=ft.Colors.GREEN_700, border_radius=10
                    )
                ),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Total Disbursed to Wards", size=16, color=ft.Colors.WHITE),
                            ft.Text("₹ 2,10,000 Cr", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ]),
                        padding=20, width=250, bgcolor=ft.Colors.BLUE_700, border_radius=10
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Village/Ward ID")),
                ft.DataColumn(ft.Text("Reported Problem")),
                ft.DataColumn(ft.Text("Assigned Funds")),
                ft.DataColumn(ft.Text("Status")),
            ],
            rows=[
                ft.DataRow(cells=[ft.DataCell(ft.Text("WARD-411011")), ft.DataCell(ft.Text("Main Road Potholes")), ft.DataCell(ft.Text("₹ 12 Lakhs")), ft.DataCell(ft.Text("Pending Verification"))]),
                ft.DataRow(cells=[ft.DataCell(ft.Text("WARD-411045")), ft.DataCell(ft.Text("Water Pipeline Leak")), ft.DataCell(ft.Text("₹ 4.5 Lakhs")), ft.DataCell(ft.Text("Funds Disbursed"))]),
                ft.DataRow(cells=[ft.DataCell(ft.Text("WARD-412301")), ft.DataCell(ft.Text("Streetlight Failure")), ft.DataCell(ft.Text("₹ 1.2 Lakhs")), ft.DataCell(ft.Text("Completed"))]),
            ]
        )
        
        back_btn = ft.TextButton(content=ft.Text("Back to Selection"), on_click=lambda _: self.build_login_screen())
        
        self.page.add(
            ft.Column(
                [
                    ft.Row([back_btn, ft.Text("Government Administrative Portal (LGD Level)", size=22, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=700),
                    ft.Divider(),
                    finance_row,
                    ft.Container(height=20),
                    ft.Text("Active Regional Projects & Grievances Queue", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(content=data_table, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=5, padding=10)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
        self.page.update()

def main(page: ft.Page):
    PragatiApp(page)

if __name__ == "__main__":
    ft.app(target=main)
